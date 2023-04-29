import openai
import json

api_key = open('openai_key', 'r')
openai.api_key = api_key.read()

language_employer = 'Spanish'
language_employee = 'English'

text : str = 'placeholder'
audio : bool = False
translation_report_context = 'You are a technician working at a company and have elaborated a report for your boss. However, your boss only speaks ' + language_employer + 'and you have to translate it. Here is the report: '
key_points_translation_context = 'You are a technician working at a company and have written 20 key points about the work you did today. However, you boss only speaks ' + language_employer + 'So you have to translate it for him. Here are the key points'
key_points_context = 'I have generated a report for my boss, but he only wants to read the 20 key points of the report, so I have to extract them. This is the report: '

def init():
    params = []
    return params

def audio_to_text():
    audio_file = open("audio.mp3", "rb")
    text = openai.Audio.transcribe("whisper-1", audio_file)
    return text['text']

def ask_gpt(input):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": input}]
        )
    output = bytes(completion.choices[0].message['content'], encoding='utf-8').decode()
    return output

def main():
    #get input data from the telegram
    key_req = 'placeholder'
    report_translation_req = 'placeholder'
    key_translation_req = 'placeholder'
    # askgpt for several things
    
    # speech to text
    if audio:
        text = audio_to_text
    
    text = "I met with the customer, Mr. Dennis Huff, who is the maintenance supervisor, to conduct an entrance interview. He told me that the machine had been down for about an hour so I could inspect some items before it resumed production of B / E double wall. I checked the lower corrugating roll and found its number W-76702, but the other roll had a lot of build up that obscured its number. I took NCR's to measure the parallelism of the corrugating rolls. The lineal counter showed 66,781,034 million lineal feet. I also looked at the roll condition briefly. I talked to the maintenance department about what they had done in the last two weeks to fix some issues with the machine. They said they had to adjust the corrugating roll parallel several times and that the roll slot wear was misaligned at ambient temperature. I checked the alignment of the corrugating rolls at heated condition and found a clear misalignment. The wear pattern on the lower corrugating roll was shifted by about two millimeters. I arranged for the machine to be cooled off for the weekly PM maintenance. I examined the corrugating rolls and saw significant plating loss on the tips and root radius of the rolls. The NCR's showed larger impressions than expected for the lineal footage on the counters. There was also a noticeable average paper width wear pattern on the rolls. When I applied 90 bar to the rolls, I saw that there was no engagement on both sides of the width for about 10 inches, centered 18 inches from the ends of the rolls. The shifting of the corrugating rolls was evident in the NCR's marks. The second resonance samples showed malformed flutes."
    key_req = key_points_context + text
    # extract key points of the text
    key_points = ask_gpt(key_req)
    print(key_points)
    # translate the report
    report_translation_req = translation_report_context + text
    report_translated = ask_gpt(report_translation_req)
    print('\n')
    print(report_translated)
    # translate the bullet points
    key_translation_req = key_points_translation_context + key_points
    key_translated = ask_gpt(key_translation_req)
    print('\n')
    print(key_translated)
    #get the trust measurement
    output = {"key_points" : key_points, "report_translated" : report_translated, "key_translated" : key_translated}
    # build pdf files
    text_file = open('output.json', 'w')
    n = text_file.write(json.dumps(output))
    text_file.close()
    # one for original language
    # another one for translation
    return True


# Execute program if not imported
if __name__ == "__main__":
    main()