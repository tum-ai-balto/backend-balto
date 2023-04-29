TITLE = 'I have generated a report for my boss, I would like you to state in one sentence what the report is about. ' \
        'Only output that specific sentence, the first word should be a noun. ' \
        'The report is in {} language, and you should also state the title in the report\'s language, ' \
        'you should not write anything that is not in that language.' \
        'This is the report: '

KEY_POINTS = 'I have generated a report for my boss, but he only wants to read some key points of the report, ' \
             'so please extract the most important ideas of this report and output them as an enumerated list. ' \
             'The report is in {} language, and you should also state the title in the report\'s language.' \
             'This is the report: '

TRANSLATED_TITLE = 'Could you translate this for me in {}? Only output the translated text, no other text.'

TRANSLATED_KEYPOINTS = 'You are a technician working at a company and have written an enumerated list of key points about the work you did today. ' \
                       'The key points are written in {} and you should translate the list to {}. Only output the translated list, do not take any contents from the original language'\
                       'Here are the key points: '

TRANSLATED_REPORT = 'You are a technician working at a company and have elaborated a report for your boss. ' \
                    'However, your boss only speaks {} and you have to translate it. Here is the report: '

RE_TRANSLATE_REPORT = "Can you translate this text from {} to {}?"