import csv
import json
import re
from os.path import exists

from wordfreq import word_frequency
import lyricsgenius

if not exists("Lyrics_AesopRock.json"):
    lyricsgenius.Genius("your API key here").search_artist("Aesop Rock").save_lyrics()

with open("Lyrics_AesopRock.json") as f:
    aes = json.load(f)

report = "aes_favorite_words.csv"

word_analysis_by_song = dict()
all_aes_words = []  # not counting 50 hours of cyphers that are only on youtube and limewire
for song in aes["songs"]:
    title = song["title"]
    if "Remix" in title:
        continue

    # remove strings like "[Chorus]"
    lyrics_without_bracketed_phrases = re.sub(r'\[.*?\]', '', song["lyrics"])
    # remove the first and last lines, which contain attribution metadata
    lyrics_without_bracketed_phrases = '\n'.join(lyrics_without_bracketed_phrases.split('\n')[1:-1])

    # what is a word? Let's say it's a group of consecutive letters which may be broken up internally by hyphens
    words_list = [word.strip('\'- ').lower() for word in re.findall('[a-zA-Z-\']+', lyrics_without_bracketed_phrases)]
    words_list = [word for word in words_list if word.replace('-', '').isalpha()]

    if len(words_list) == 0:
        continue
    all_aes_words.extend(words_list)
    unique_words_in_this_song = list(set(words_list))
    word_analysis_by_song[title] = dict()
    for word in unique_words_in_this_song:
        word_analysis_by_song[title][word] = {'freq_en': word_frequency(word, lang='en')}

for song in word_analysis_by_song:
    for word in word_analysis_by_song[song]:
        word_analysis_by_song[song][word]['freq_aes'] = all_aes_words.count(word) / len(all_aes_words)
        try:
            word_analysis_by_song[song][word]['preference_aes'] = word_analysis_by_song[song][word]['freq_aes'] / \
                                                                  word_analysis_by_song[song][word]['freq_en']
        except ZeroDivisionError:
            word_analysis_by_song[song][word]['preference_aes'] = None


# make a list of word, preference tuples [("word", 2.503203), ...] and sort descending by preference
word_preferences = list(
    set([(word, word_analysis_by_song[song][word]['preference_aes']) for song in word_analysis_by_song for word in word_analysis_by_song[song] if word_analysis_by_song[song][word]['preference_aes'] is not None]))
favorite_words = sorted(word_preferences, key=lambda t: t[1], reverse=True)

with open(report, 'w', newline='\n') as out_fp:
    o = csv.writer(out_fp)
    o.writerow(["word", "preference", "occurrences", "song_count", "songs"])
    for word, preference in favorite_words:
        song_appearances = [song.replace('\u200b', '') for song in word_analysis_by_song if
                            word in word_analysis_by_song[song]]
        o.writerow([word, preference, all_aes_words.count(word), len(song_appearances), '; '.join(song_appearances)])
