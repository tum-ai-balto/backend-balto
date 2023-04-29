import openai
import json
import os, sys, time
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
    audio_file = open("audio.mp3", "rb")
    text = openai.Audio.transcribe("whisper-1", audio_file)
    return text['text']


def ask_gpt(gpt_prompt: str) -> str:
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": gpt_prompt}])
    output = bytes(completion.choices[0].message['content'], encoding='utf-8').decode()
    return output


def extract_report_from_msg(messages: GenerateReportMessageRequest) -> str:
    text = ""

    for msg in messages.chatMessages:
        if msg.kind == EmployeeMessage.Kind.IMAGE:
            # Download the image from msg.content
            pass
        elif msg.kind == EmployeeMessage.Kind.AUDIO:
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
    return

def on_incoming_msg(_channel, _method, _properties, body) -> None:

    incoming_msg = GenerateReportMessageRequest.from_json(body)
    employer_lang = language_tag_to_name(incoming_msg.employer_language)
    employee_lang = language_tag_to_name(incoming_msg.employee_language)
    print(f"[info] :: employee '{incoming_msg.employee}' ({employee_lang}) is sending a message to the employer '{incoming_msg.employer}' ({employer_lang})...")

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
        'title': generated_title,
        'report': report,
        'keypoints': generated_keypoints,
        'translated_title': translated_title,
        'translated_report': translated_report,
        'translated_keypoints': translated_keypoints
    }

    # Store the message for analysis
    dump_incoming_message(created_content)

    # Generate PDF file


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
        main()
    except KeyboardInterrupt:
        sys.exit(0)
