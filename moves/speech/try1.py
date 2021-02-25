from os.path import join

from pocketsphinx import LiveSpeech
from pocketsphinx import get_model_path
from speech_recognition import Microphone
from speech_recognition import Recognizer


def main_ps() -> None:
    model_path = get_model_path()
    print(f'{model_path=}')

    for phrase in LiveSpeech(verbose=True,
                             hmm=join(model_path, 'it-it'),
                             lm=join(model_path, 'it-it.lm.bin'),
                             dict=join(model_path, 'cmudict-it-it.dict')):
        print(f'{str(phrase)=}')


def main_sr() -> None:
    recognizer = Recognizer()
    microphone = Microphone()

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)

    while True:
        with microphone as source:
            text = recognizer.recognize_sphinx(recognizer.listen(source),
                                               language='it-IT',
                                               keyword_entries=[(f'{l}{n}', 1)
                                                                for l in 'abcdefgh'
                                                                for n in range(1, 9)])

            print(f'{text=}')
            if text == 'stop':
                break


main = main_ps

if __name__ == '__main__':
    main()
