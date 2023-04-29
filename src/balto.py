import openai
import json
import os, sys, time, re, base64
import pika
import gpt_contexts
import pdfkit
import score

from langcodes import Language
from message import GenerateReportMessageRequest, EmployeeMessage

# 10789

RABBIT_MQ = 'ssh.grassi.dev'
INCOMING_MSG_QUEUE = 'incoming-msgs'
OUTGOING_MSG_QUEUE = 'outgoing-msgs'
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")


def score_to_color(accuracy: float) -> str:
    if accuracy <= 0.1:
        return "#ff0000"
    elif accuracy <= 0.3:
        return "#ff4c4c"
    elif accuracy <= 0.5:
        return "#ffd424"
    elif accuracy <= 0.7:
        return "#ddff24"
    else:
        return "#56ff24"


def language_tag_to_name(tag: str) -> str:
    return Language.make(tag).display_name()


def audio_to_text(audio_url: str) -> str:
    # telegram_endpoint = f"https://api.telegram.org/bot{audio_url}"

    with open("../audio/sample.mp3", "rb") as audio_file:
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
            text += audio_to_text(msg.content)
        elif msg.kind == EmployeeMessage.Kind.TEXT:
            text += msg.content
        text += "\n"

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
    bullet_points = filter(lambda l: re.match("[0-9]+", l), content['keypoints'].split("\n"))
    bullet_points = ''.join(map(lambda l: f"<li>{re.split('[0-9]+. +', l)[1]}</li>", bullet_points))
    translated_bullet_points = filter(lambda l: re.match("[0-9]+", l), content['translated_keypoints'].split("\n"))
    translated_bullet_points = ''.join(
        map(lambda l: f"<li>{re.split('[0-9]+. +', l)[1]}</li>", translated_bullet_points))

    images = list(map(lambda i: f"<img width='300' src='{i}' />", content['images']))

    translated_content = "<html><head><meta charset='utf-8'><style>* { font-family: 'system-ui', sans-serif; text-align: justify; }</style></head><body>"
    translated_content += f"<h1>Company Name</h1>" \
                          f"<h2>{content['employee']}</h2>"
    translated_content += f"<h3>{content['translated_title']}</h3>"
    translated_content += f"<p><b>Score</b>: {content['accuracy']}</p>"
    translated_content += f"<p><b>Report:</b><br>{content['translated_report']}</p>"
    translated_content += f"<p><b>Key points:</b><br><ol>{translated_bullet_points}</ol></p>"
    translated_content += f"<h3>{content['title']}</h3>"
    translated_content += f"<p><b>Score</b>: {content['accuracy']}</p>"
    translated_content += f"<p><b>Report:</b><br>{content['report']}</p>"
    translated_content += f"<p><b>Key points:</b><br><ol>{bullet_points}</ol></p>"

    if len(images) > 0:
        translated_content += f"<div><h4>Media</h4>{''.join(images)}</div>"

    translated_content += "</body></html>"

    pdf_path = f"../pdfs/pdf-{time.time_ns()}.pdf"
    pdfkit.from_string(translated_content, pdf_path, options=pdf_options)

    return pdf_path


def on_incoming_msg(_channel, _method, _properties, body) -> None:
    print("[info] :: incoming message...")

    incoming_msg = GenerateReportMessageRequest.from_json(body)
    images = list(
        map(lambda x: x.content, filter(lambda x: x.kind == EmployeeMessage.Kind.IMAGE, incoming_msg.chat_messages)))

    employer_lang = language_tag_to_name(incoming_msg.employer_language)
    employee_lang = language_tag_to_name(incoming_msg.employee_language)
    print(
        f"[info] :: employee '{incoming_msg.employee}' ({employee_lang}) is sending a message to the employer '{incoming_msg.employer}' ({employer_lang})...")

    report = extract_report_from_msg(incoming_msg)

    gpt_prompt = build_gpt_prompt(gpt_contexts.RE_TRANSLATE_REPORT.format('english', employee_lang), gpt_contexts.TITLE)
    translated_prompt = ask_gpt(gpt_prompt)

    gpt_prompt = build_gpt_prompt(translated_prompt, report)
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

    gpt_prompt = build_gpt_prompt(gpt_contexts.RE_TRANSLATE_REPORT.format(employer_lang, employee_lang),
                                  translated_report)
    re_translated_report = ask_gpt(gpt_prompt)

    scores, accuracy = score.calculate_fidelity(report, re_translated_report)
    print(f"[info] :: accuracy computed = {accuracy}, scores = {scores}")
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
        'images': images,
        'accuracy': str(accuracy)
    }

    # Store the message for analysis
    dump_incoming_message(created_content)

    # Generate PDF file
    pdf_path = generate_pdf_report(created_content)
    with open(pdf_path, 'rb') as pdf:
        created_content['pdf'] = base64.b64encode(pdf.read()).decode('ascii')

    _channel.basic_publish(exchange='', routing_key=OUTGOING_MSG_QUEUE, body=json.dumps(created_content))


def main():
    print("[info] :: connecting to RabbitMQ for handling messages...")

    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBIT_MQ))
    channel = connection.channel()

    # Declare an incoming and outgoing for queues
    channel.queue_declare(INCOMING_MSG_QUEUE)
    channel.queue_declare(OUTGOING_MSG_QUEUE)

    channel.basic_consume(queue=INCOMING_MSG_QUEUE, auto_ack=True, on_message_callback=on_incoming_msg)

    print("[info] :: start main message loop...")
    channel.start_consuming()


# Execute program if not imported
if __name__ == "__main__":
    # Set up OpenAI key
    openai.api_key = os.getenv('OPENAI_KEY')
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
