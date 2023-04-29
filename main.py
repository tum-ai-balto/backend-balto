import cohere

api_key = open('cohere_key', 'r')
co = cohere.Client(api_key.read())


language = 'Spanish'
text : str = 'placeholder'
audio : bool = False
context_prompt = 'You are a technician working at a company and have elaborated a report for your boss. However, your boss only speaks ' + language + 'and you have to translate it. Here is the report: '

# if audio:
#     audio_file = open("audio.mp3", "rb")
#     text = openai.Audio.transcribe("whisper-1", audio_file)
# else:
#     text = open('text.txt')

#remove from here
text = "I met with the customer, Mr. Dennis Huff, who is the maintenance supervisor, to conduct an entrance interview. He told me that the machine had been down for about an hour so I could inspect some items before it resumed production of B / E double wall. I checked the lower corrugating roll and found its number W-76702, but the other roll had a lot of build up that obscured its number. I took NCR's to measure the parallelism of the corrugating rolls. The lineal counter showed 66,781,034 million lineal feet. I also looked at the roll condition briefly. I talked to the maintenance department about what they had done in the last two weeks to fix some issues with the machine. They said they had to adjust the corrugating roll parallel several times and that the roll slot wear was misaligned at ambient temperature. I checked the alignment of the corrugating rolls at heated condition and found a clear misalignment. The wear pattern on the lower corrugating roll was shifted by about two millimeters. I arranged for the machine to be cooled off for the weekly PM maintenance. I examined the corrugating rolls and saw significant plating loss on the tips and root radius of the rolls. The NCR's showed larger impressions than expected for the lineal footage on the counters. There was also a noticeable average paper width wear pattern on the rolls. When I applied 90 bar to the rolls, I saw that there was no engagement on both sides of the width for about 10 inches, centered 18 inches from the ends of the rolls. The shifting of the corrugating rolls was evident in the NCR's marks. The second resonance samples showed malformed flutes."
#input = context_prompt + text

input = context_prompt + text

response = co.generate(
  model='command',
  prompt=input,
  max_tokens=700,
  temperature=0,
  k=0,
  stop_sequences=[],
  return_likelihoods='NONE')
print('Prediction: {}'.format(response.generations[0].text))
print('\n\n')

key_points_1 = 'I have generated a report for my boss, but he only wants to read the 20 key points of the report, so I have to extract them. This is the report: '
key_points_2 = 'And the 20 key points I extracted from the text are: '

key_points = key_points_1 + text + key_points_2

response = co.generate(
  model='command',
  prompt=key_points,
  max_tokens=700,
  temperature=0,
  k=0,
  stop_sequences=[],
  return_likelihoods='NONE')
print('Prediction: {}'.format(response.generations[0].text))

key_points = response.generations[0].text
translate_key_points = 'I have written some text for my boss, explaining the main points of the work I have done today. However, my boss only speaks ' + language + 'so I would like to translate them for him. These are the key points: '

key_points_translate = translate_key_points+key_points
response = co.generate(
  model='command',
  prompt=key_points_translate,
  max_tokens=700,
  temperature=0,
  k=0,
  stop_sequences=[],
  return_likelihoods='NONE')
print('Prediction: {}'.format(response.generations[0].text))