import openai
import json
import os, sys, time, re
import pika
import gpt_contexts
import pdfkit

from langcodes import Language
from message import GenerateReportMessageRequest, EmployeeMessage

RABBIT_MQ = 'localhost'
INCOMING_MSG_QUEUE = 'incoming-msgs'
OUTGOING_MSG_QUEUE = 'outgoing-msgs'


def language_tag_to_name(tag: str) -> str:
    return Language.make(tag).display_name()


def audio_to_text():
    text = ""
    with open("audio.mp3", "rb") as audio_file:
        text = openai.Audio.transcribe("whisper-1", audio_file)

    return text['text']


def ask_gpt(gpt_prompt: str) -> str:
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": gpt_prompt}])
    output = bytes(completion.choices[0].message['content'], encoding='utf-8').decode()
    return output


def extract_report_from_msg(messages: GenerateReportMessageRequest) -> str:
    text = ""

    for msg in messages.chat_messages:
        if msg.kind == EmployeeMessage.Kind.AUDIO:
            # Download the audio from msg.content
            pass
        elif msg.kind == EmployeeMessage.Kind.TEXT:
            text += msg.content

    return text


def build_gpt_prompt(context: str, msg: str) -> str:
    return f"{context} '{msg}'"


def dump_incoming_message(content):
    reports_folder = '../reports/'
    if not os.path.exists(reports_folder):
        os.mkdir(reports_folder)

    filename = f"report-{time.time_ns()}.json"
    final_path = os.path.join(reports_folder, filename)

    with open(final_path, 'w') as output_file:
        output_file.write(json.dumps(content))
    print(f"[info] :: write report to file '{final_path}'")


def generate_pdf_report(content):
    pdf_options = {
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
    }

    bullet_points = filter(lambda l: re.match("[0-9]+", l), content['translated_keypoints'].split("\n"))
    bullet_points = ''.join(map(lambda l: f"<li>{re.split('[0-9]+. +', l)[1]}</li>", bullet_points))

    images = list(map(lambda i: f"<img width='300' src='{i}' />", content['images']))

    translated_content = "<html><head><meta charset='utf-8'><style>* { font-family: 'system-ui', sans-serif; text-align: justify; }</style></head><body>"
    translated_content += f"<h1>Company Name</h1>" \
                          f"<h2>{content['employee']}</h2>"
    translated_content += f"<h3>{content['translated_title']}</h3>"
    translated_content += f"<p><b>Report:</b><br>{content['translated_report']}</p>"
    translated_content += f"<p><b>Key points:</b><br><ol>{bullet_points}</ol></p>"
    translated_content += f"<div><h4>Media</h4>{''.join(images)}</div>"

    translated_content += "</body></html>"

    pdfkit.from_string(translated_content, f"../pdfs/pdf-{time.time_ns()}.pdf", options=pdf_options)

    return


def on_incoming_msg(_channel, _method, _properties, body) -> None:
    incoming_msg = GenerateReportMessageRequest.from_json(body)
    images = list(
        map(lambda x: x.content, filter(lambda x: x.kind == EmployeeMessage.Kind.IMAGE, incoming_msg.chat_messages)))

    employer_lang = language_tag_to_name(incoming_msg.employer_language)
    employee_lang = language_tag_to_name(incoming_msg.employee_language)
    print(
        f"[info] :: employee '{incoming_msg.employee}' ({employee_lang}) is sending a message to the employer '{incoming_msg.employer}' ({employer_lang})...")

    report = extract_report_from_msg(incoming_msg)
    gpt_prompt = build_gpt_prompt(gpt_contexts.TITLE.format(employee_lang), report)
    generated_title = ask_gpt(gpt_prompt)
    print(f"[info] :: generated title from text: '{generated_title}'")

    gpt_prompt = build_gpt_prompt(gpt_contexts.KEY_POINTS.format(employee_lang), report)
    generated_keypoints = ask_gpt(gpt_prompt)

    gpt_prompt = build_gpt_prompt(gpt_contexts.TRANSLATED_TITLE.format(employer_lang), generated_title)
    translated_title = ask_gpt(gpt_prompt)
    print(f"[info] :: translated title: '{generated_title}' -> '{translated_title}'")

    gpt_prompt = build_gpt_prompt(gpt_contexts.TRANSLATED_KEYPOINTS.format(employer_lang, employer_lang),
                                  generated_keypoints)
    translated_keypoints = ask_gpt(gpt_prompt)
    gpt_prompt = build_gpt_prompt(gpt_contexts.TRANSLATED_REPORT.format(employer_lang), report)
    translated_report = ask_gpt(gpt_prompt)

    print(f"[info] :: generation complete. Dumping the message content on the filesystem...")

    created_content = {
        'employer': incoming_msg.employer,
        'employee': incoming_msg.employee,
        'title': generated_title,
        'report': report,
        'keypoints': generated_keypoints,
        'translated_title': translated_title,
        'translated_report': translated_report,
        'translated_keypoints': translated_keypoints,
        'images': images
    }

    # Store the message for analysis
    dump_incoming_message(created_content)

    # Generate PDF file
    generate_pdf_report(created_content)


def main():
    print("[info] :: connecting to RabbitMQ for receiving messages...")

    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBIT_MQ))
    channel = connection.channel()

    # Declare an incoming and outgoing for queues
    channel.queue_declare(INCOMING_MSG_QUEUE)
    channel.queue_declare(OUTGOING_MSG_QUEUE)

    channel.basic_consume(queue=INCOMING_MSG_QUEUE, auto_ack=True, on_message_callback=on_incoming_msg)

    channel.start_consuming()


# Execute program if not imported
if __name__ == "__main__":
    # Set up OpenAI key
    openai.api_key = os.getenv('OPENAI_KEY')
    try:
        # main()
        test_msg = GenerateReportMessageRequest('John Doe', 'Maria Garcia', 'en', 'es', [
            EmployeeMessage(EmployeeMessage.Kind.TEXT,
                            "I met with the customer, Mr. Dennis Huff, who is the maintenance supervisor, to conduct an entrance interview. He told me that the machine had been down for about an hour so I could inspect some items before it resumed production of B / E double wall. I checked the lower corrugating roll and found its number W-76702, but the other roll had a lot of build up that obscured its number. I took NCR's to measure the parallelism of the corrugating rolls. The lineal counter showed 66,781,034 million lineal feet. I also looked at the roll condition briefly. I talked to the maintenance department about what they had done in the last two weeks to fix some issues with the machine. They said they had to adjust the corrugating roll parallel several times and that the roll slot wear was misaligned at ambient temperature. I checked the alignment of the corrugating rolls at heated condition and found a clear misalignment. The wear pattern on the lower corrugating roll was shifted by about two millimeters. I arranged for the machine to be cooled off for the weekly PM maintenance. I examined the corrugating rolls and saw significant plating loss on the tips and root radius of the rolls. The NCR's showed larger impressions than expected for the lineal footage on the counters. There was also a noticeable average paper width wear pattern on the rolls. When I applied 90 bar to the rolls, I saw that there was no engagement on both sides of the width for about 10 inches, centered 18 inches from the ends of the rolls. The shifting of the corrugating rolls was evident in the NCR's marks. The second resonance samples showed malformed flutes."),
            EmployeeMessage(EmployeeMessage.Kind.IMAGE,
                            "https://png.pngtree.com/png-clipart/20220716/ourmid/pngtree-banana-yellow-fruit-banana-skewers-png-image_5944324.png"),
            EmployeeMessage(EmployeeMessage.Kind.IMAGE,
                            "https://banner2.cleanpng.com/20180524/tqg/kisspng-llama-alpaca-camel-drawing-5b073e5101e844.6911836915272013610078.jpg"),
        ])
        on_incoming_msg(None, None, None, test_msg.to_json())
    except KeyboardInterrupt:
        sys.exit(0)
