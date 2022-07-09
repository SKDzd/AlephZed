# AlephZed: Bilingual Hangman game (Arabic-English)
# (c) SKDzd , email on yahoo: SalamaCast
# v0.1 (23-30/4/2022), v0.2 (27-30/5), v0.3 (31/5), v0.4 (4-13/6)

# TODO:
# Success & Failure feedback messages/images
# Flask: login/Session for high-score recording
# TTS for final English words? Not Likely. Audio feedback (e.g. beeps)
# flask-SqlAlchemy. Remove dependency on 'session cookies' for the solved list(s),
# because the browser max cookie size is 4kb
# Qt GUI, maybe

# Note: Slicing fixes out of range indexing errors
# FIXME:
# Doesn't work well on combined words (e.g. stronghold), "ch" as "k" sounds (anchor), 
# "s" as "z" (busy, bees), "gh" as "g" or "f" (aghast/laugh), so avoid them in the wordlist
# possibly use an IPA-aware dictionary or Carnegie Pronouncing Dictionary cmudict.0.6?
# but those replace whole syllables, not letter-for-letter.
# Silent letters: i(s)land, lis(t)en, wres(t)ling, adventur(e), (h)eir, etc.
# x(iou)s = ش

import re, random
from flask import Flask, render_template, request, url_for, session, redirect


app = Flask(__name__)
app.secret_key = "Qhlv01xR3r"

# Global Dictionary
the_dic = {}
with open("wl.txt") as f:
    lines = f.readlines()
for line in lines:
    # to exclude empty lines
    if ":" in line:
        # Now the dict() is actually En --> Ar Dictionary
        e,a = line.strip().split(":")
        the_dic[e] = a
length = len(the_dic)

def settingUp():
    ''' Preparations for starting a new round '''
    
    if not session:
        # session.new didn't work. why?
        session["solved"] = []
        session["solved_couples"] = []
                
    # random() works only on sequences, hence the conversion to list
    session["chosen_word"] = random.choice(list(the_dic))
    
    # to exclude the already solved
    if session["solved"] and session["chosen_word"] in session["solved"]:
        while True:
            session["chosen_word"] = random.choice(list(the_dic))
            if not session["chosen_word"] in session["solved"]:
                break
    
    session["wordEn"] = session["chosen_word"].upper()
    session["wordAr"] = the_dic[session["chosen_word"]]
    session["blank_list_en"] = ['-'] * len(session["wordEn"])
    session["tries"] = 8
    
    # For drawing template buttons
    # the middle element is set-up for a trick to DISABLE the btn, by adding to the tag, w/o JS
    # Template button loop: <button name="the_harf" value="{{btn[0]}}" {{btn[1]}}>{{btn[2]}}</button>
    session["buttons"] = [
            ["ب","","ب"],
            ["ت","","ت"],
            ["ث","","ث"],
            ["ج","","ج"],
            ["د","","د"],
            ["ذ","","ذ"],
            ["ر","","ر"],
            ["ز","","ز"],
            ["س","","س"],
            ["ش","","ش"],
            ["ف","","ف"],
            ["ك","","ك"],
            ["ل","","ل"],
            ["م","","م"],
            ["ن","","ن"],
            ["ه","","هـ"],
            ["0","","ا/و/ي"],
            ]
    
#    # for space-separated 2-word Arabic wordlist entries
#    for indx_ar, letter_ar in enumerate(session["wordAr"]):
#        if letter_ar == " ":
#            session["blank_list_ar"][indx_ar] = " "
    
    # for English letters with no Arabic equivalent
    for indx_en, letter_en in enumerate(session["wordEn"]):
        if letter_en in "VX":
            session["blank_list_en"][indx_en] = letter_en
    # flag(s)
    session["round_in_progress"] = True


def letterConverter(ArabicLetter, EnglishWord):
    ''' Checks for Phonetic Equivalents between Arabic letters & English syllables '''
    
    ltr = ArabicLetter
    word = EnglishWord
    one_for_one_letters = {"ا":"A","د":"D","ز":"Z","ل":"L","م":"M"}
    blank_list_en = session["blank_list_en"]
    
    if ltr in "حخصضطظعغق":
        return # No English equivalent
    elif ltr in one_for_one_letters:
        eng_ltr = one_for_one_letters[ltr]
        for indx,letter in enumerate(word):
            if letter == eng_ltr:
                blank_list_en[indx] = eng_ltr
    elif ltr == "ر":
        for indx,letter in enumerate(word):
            if letter == "R":
                blank_list_en[indx] = letter
                if indx == 1 and word[:indx+1] == "WR":
                    blank_list_en[:2] = "WR"
    elif ltr == "ن":
        for indx,letter in enumerate(word):
            if letter == "N":
                blank_list_en[indx] = letter
                if indx == 1 and word[:indx+1] == "KN":
                    blank_list_en[:2] = "KN"
    elif ltr == "ف":
        for indx,letter in enumerate(word):
            if letter == "F": blank_list_en[indx] = letter
            elif letter == "P" and word[indx:indx+2] == "PH":
                blank_list_en[indx:indx+2] = "PH"
    elif ltr == "و":
        for indx,letter in enumerate(word):
            if letter == "W":
                if indx == 0 and word[indx:indx+2] == "WR": continue
                blank_list_en[indx] = letter
                if word[:2] == "WH":
                    blank_list_en[:2] = "WH"
            if letter == "U":
                itr = re.finditer("TIOUS|CIOUS|TURE", word)
                if itr:
                    for m in itr:
                        if indx in range(m.start(), m.end()):
                            break
                    else:
                        blank_list_en[indx] = letter
                        if word[indx:indx+3] == "UGH":
                            blank_list_en[indx:indx+3] = "UGH"
                else:
                    blank_list_en[indx] = letter
                    if word[indx:indx+3] == "UGH":
                        blank_list_en[indx:indx+3] = "UGH"
            elif letter == "O":
                itr = re.finditer("TION|SION|TIOUS|CIOUS", word)
                if itr:
                    for m in itr:
                        if indx in range(m.start(), m.end()):
                            break
                    else:
                        blank_list_en[indx] = letter
                else:
                    blank_list_en[indx] = letter
    elif ltr == "ي":
        for indx,letter in enumerate(word):
            if letter in "EY": blank_list_en[indx] = letter
            elif letter == "I":
                itr = re.finditer("TION|SION|TIOUS|CIOUS", word)
                if itr:
                    for m in itr:
                        if indx in range(m.start(), m.end()):
                            break
                    else:
                        blank_list_en[indx] = letter
                        if word[indx:indx+3] == "IGH":
                            blank_list_en[indx:indx+3] = "IGH"
                else:
                    blank_list_en[indx] = letter
                    if word[indx:indx+3] == "IGH":
                        blank_list_en[indx:indx+3] = "IGH"
    elif ltr == "ب":
        for indx,letter in enumerate(word):
            if letter == "B": blank_list_en[indx] = letter
            elif letter == "P":
                if indx == 0 and word[1] == "S": continue
                elif word[indx:indx+2] == "PH": continue
                blank_list_en[indx] = letter
    elif ltr == "ت":
        for indx,letter in enumerate(word):
            if letter == "T":
                if word[indx:indx+2] == "TH": continue
                elif word[indx:indx+4] == "TION": continue
                elif word[indx:indx+5] == "TIOUS": continue
                elif word[indx:indx+4] == "TURE": continue
                blank_list_en[indx] = letter
    elif ltr == "ث":
        for indx,letter in enumerate(word):
            if letter == "T" and word[indx:indx+2] == "TH":
                itr = re.finditer(".THER", word)
                if itr:
                    for m in itr:
                        if indx == m.start() + 1:
                            break
                    else:
                        blank_list_en[indx:indx+2] = "TH"
                else:
                    blank_list_en[indx:indx+2] = "TH"
    elif ltr == "ج":
        for indx,letter in enumerate(word):
            if letter == "J": blank_list_en[indx] = letter
            elif letter == "G":
                if word[indx:indx+2] == "GH": continue
                blank_list_en[indx] = letter
    elif ltr == "ذ":
        itr = re.finditer(".THER", word)
        if itr:
            for m in itr:
                blank_list_en[m.start()+1:m.start()+4] = "THE"
    elif ltr == "س":
        for indx,letter in enumerate(word):
            if letter == "C":
                if word[indx:indx+3] == "CIA": continue
                if word[indx:indx+5] == "CIOUS": continue
                itr = re.finditer("C[EIY]", word)
                if itr:
                    for m in itr:
                        if indx == m.start():
                            blank_list_en[indx] = letter
            elif letter == "S":
                if word[indx:indx+2] == "SH": continue
                if indx == 1 and word[0] == "P":
                    blank_list_en[:2] = "PS"
                itr = re.finditer("[S]?SION|[S]?SUR[AEI]", word)
                if itr:
                    for m in itr:
                        if indx in range(m.start(), m.end()):
                            break
                    else:
                        blank_list_en[indx] = letter
                else:
                    blank_list_en[indx] = letter
    elif ltr == "ش":
        for indx,letter in enumerate(word):
            if letter == "C":
                if word[indx:indx+5] == "CIOUS":
                    blank_list_en[indx:indx+4] = "CIOU"
                elif word[indx:indx+3] == "CIA":
                    blank_list_en[indx] = letter
                    if word[indx:indx+4] == "CIAN":
                        blank_list_en[indx:indx+3] = "CIA"
                elif word[indx:indx+2] == "CH" and not word[indx:indx+3] == "CHR":
                    blank_list_en[indx:indx+2] = "CH"
            elif letter == "T":
                itr1 = re.finditer("TION|TIOUS", word)
                itr2 = re.finditer("TURE", word)
                if itr1:
                    for m in itr1:
                        blank_list_en[m.start():m.end()-1] = word[m.start():m.end()-1]
                if itr2:
                    for m in itr2:
                        blank_list_en[m.start():m.start()+2] = "TU"
            elif letter == "S":
                if word[indx:indx+2] == "SH":
                    blank_list_en[indx:indx+2] = "SH"
                itr1 = re.finditer("[S]?SION", word)
                if itr1:
                    for m in itr1:
                        blank_list_en[m.start():m.end()-1] = word[m.start():m.end()-1]
                itr2 = re.finditer("[S]?SUR[AEI]", word)
                if itr2:
                    for m in itr2:
                        blank_list_en[m.start():m.end()-2] = word[m.start():m.end()-2]
    elif ltr == "ه":
        itr = re.finditer("TH|PH|GH|SH|CH|WH", word)
        for indx,letter in enumerate(word):
            if letter == "H":
                if itr:
                    for m in itr:
                        if indx in range(m.start(), m.end()):
                            break
                    else:
                        blank_list_en[indx] = letter
                else:
                    blank_list_en[indx] = letter
    elif ltr == "ك":
        for indx,letter in enumerate(word):
            if letter == "C":
                if word[indx:indx+2] == "CK":
                    blank_list_en[indx:indx+2] = "CK"
                    continue
                elif word[indx:indx+3] == "CHR":
                    blank_list_en[indx:indx+2] = "CH"
                    continue
                else:
                    itr = re.finditer("C[EIYH]", word)
                    if itr:
                        for m in itr:
                            if indx in range(m.start(), m.end()):
                                break
                        else:
                            blank_list_en[indx] = letter
                    else:
                        blank_list_en[indx] = letter
            elif letter == "Q":
                blank_list_en[indx] = letter
            elif letter == "K":
                if indx == 0 and word[indx:indx+2] == "KN": continue
                else:
                    blank_list_en[indx] = letter
    else:
        pass

#def hangmanArabic(ArabicLetter, ArabicWord, EnglishWord):
#    ''' regular Arabic Hangman + calling Ar-En letter converter '''
#    special_forms = {"أ":"ا", "ء":"ا", "ؤ":"و", "ى":"ي", "ئ":"ي", "ة":"ه", "آ":"ا", "إ":"ا"}
#    ltr_ar = ArabicLetter
#    
#    for dx,l in enumerate(ArabicWord):
#        if l in special_forms:
#            l = special_forms[l]
#        if l == ltr_ar:
#            session["blank_list_ar"][dx] = ArabicWord[dx]
#    
#    letterConverter(ArabicLetter, EnglishWord)

@app.route("/cleanse")
def cleanse():
    session.clear()
    return redirect(url_for("game"))

@app.route("/totalVictory")
def totalVictory():
    return render_template("victory.html", solved_couples=reversed(session["solved_couples"]), length=length)

@app.route("/", methods=["GET", "POST"])
def game():
    ''' main function '''
    
    if not "round_in_progress" in session:
        settingUp()
        
    if request.method == "POST":
        # Before/After comparision, for scoring. pt1
        lst_en_before = tuple(session["blank_list_en"])
        
        # from template. Do requests need to be global session variables?
        harf = request.form["the_harf"]
        if harf == "0":
            # Vowels button
            for h in "اوي":
                letterConverter(h, session["wordEn"])
        elif harf == "1":
            # cheating
            for h2 in "ابتثجدذرزسشفكلمنهوي":
                letterConverter(h2, session["wordEn"])
        else:
            letterConverter(harf, session["wordEn"])
        
        # For disabling pressed template buttons
        for d,h3 in enumerate("بتثجدذرزسشفكلمنه0"):
            if harf == h3:
                session["buttons"][d][1] = "disabled"
        
        # Before/After comparision, for scoring. pt2
        lst_en_after = tuple(session["blank_list_en"])
        # Comparing mutables in this case doesn't work, hence the tuple conversion
        if lst_en_before == lst_en_after:
            session["tries"] -= 1
        
        # Failure
        if session["tries"] == 0:
            session.pop("round_in_progress")
            return redirect(url_for("game"))
        
        # Success
        # Can't use blanksEn here *before* updating/joining the strings
        if session["blank_list_en"] == list(session["wordEn"]):
            session.pop("round_in_progress")
            session["solved"].append(session["chosen_word"])
            # for the template's "Solved" column
            session["solved_couples"].append(session["chosen_word"].title() + " " + the_dic[session["chosen_word"]])
            # Total Victory. Exhausted Dictionary
            if len(session["solved"]) == length: return redirect(url_for("totalVictory"))

            return redirect(url_for("game"))
    
    session["blanksEn"] = ''.join(session["blank_list_en"])
    
    # for terminal debugging
#    print(session["wordEn"], session["wordAr"], sep=" ")
#    print(session["blanksEn"])
#    print(session["tries"])
    print(dict(session))
    print()
    
    return render_template(
            "index.html", blanksEn=session["blanksEn"], wordAr=session["wordAr"], 
            tries=session["tries"], solved_couples=reversed(session["solved_couples"]), 
            buttons=session["buttons"], length=length)

if __name__ == '__main__':
    app.run()
