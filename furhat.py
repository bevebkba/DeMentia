from furhat_realtime_api import FurhatClient
import logging
import random


ROBOT_IP = "127.0.0.1"
CHARACTER = "Titan (Adult)"
STARTING_USER_HAPPINESS = 0.5
EXERCISE_HAPPINESS_THRESHOLD = 0.6


class FurhatRobot:
    def __init__(self, robot_ip, character):
        self.robot_ip = robot_ip
        self.character = character
        self.client = FurhatClient(robot_ip)
        self.client.set_logging_level(logging.INFO)

    def connect(self):
        self.client.connect()

    def disconnect(self):
        self.client.disconnect()
        print("Disconnected")

    def setup_face(self):
        try:
            self.client.request_face_config(
                face_id=self.character,
                visibility=True,
                microexpressions=True,
            )
        except Exception:
            # Character name can differ between Furhat installations.
            self.client.request_face_config(
                face_id=self.character,
                visibility=True,
                microexpressions=True,
            )

    def setup_listening(self):
        self.client.request_listen_config(
            languages=["en-US"],
            phrases=[
                "what is on my agenda today",
                "let's do an exercise",
                "agenda",
                "exercise",
                "apple",
                "river",
                "jacket",
                "i don't know",
                "okay",
                "yes",
                "no",
            ],
        )

    def say(self, text):
        print(f"Furhat: {text}")
        self.client.request_speak_text(text, wait=True, abort=True)

    def listen(self):
        heard = self.client.request_listen_start(
            partial=False,
            concat=True,
            stop_no_speech=True,
            stop_user_end=True,
            no_speech_timeout=8.0,
            end_speech_timeout=1.0,
        )
        heard = heard or ""
        heard = heard.lower().strip()
        print(f"User: {heard}")
        return heard

    def gesture(self, name, intensity=1.0, duration=1.0, wait=True):
        try:
            self.client.request_gesture_start(
                name,
                intensity=intensity,
                duration=duration,
                wait=wait,
            )
        except Exception:
            pass



class Intents:
    AFFIRM = "affirm"
    DENY = "deny"
    REPEAT = "repeat"
    UNKNOWN = "unknown"
    AGENDA = "agenda"
    EXERCISE = "exercise"
    GREETING = "greeting"
    HELP = "help"
    EXIT = "exit"
    FALLBACK = "fallback"

    PHRASES = {
        AFFIRM: [
            "yes",
            "yeah",
            "yep",
            "okay",
            "ok",
            "sure",
            "of course",
            "alright",
            "go ahead",
            "sounds good",
        ],
        DENY: [
            "no",
            "nope",
            "nah",
            "stop",
            "not now",
            "later",
            "dont",
            "don't",
            "dont want",
            "don't want",
            "do not",
            "do not want",
            "not really",
            "cancel",
        ],
        REPEAT: [
            "huh",
            "what",
            "what do you mean",
            "again",
            "repeat",
            "can you repeat",
            "say that again",
            "i don't understand",
            "i dont understand",
        ],
        UNKNOWN: [
            "i don't know",
            "i dont know",
            "i dont remember",
            "i don't remember",
            "don't know",
            "dont know",
            "not sure",
            "i am not sure",
        ],
        AGENDA: [
            "agenda",
            "what is on my agenda",
            "what is on my agenda today",
            "schedule",
            "what should i do today",
            "what do i have today",
        ],
        EXERCISE: [
            "exercise",
            "let's do an exercise",
            "lets do an exercise",
            "training",
            "practice",
            "memory exercise",
        ],
        GREETING: [
            "hello",
            "hi",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
        ],
        HELP: [
            "help",
            "what can you do",
            "what should i say",
            "how does this work",
        ],
        EXIT: [
            "bye",
            "goodbye",
            "exit",
            "quit",
            "finish",
            "close",
            "see you",
        ],
    }


class IntentMatcher:
    @staticmethod
    def normalize(text):
        return (text or "").lower().strip()

    @staticmethod
    def detect(text):
        text = IntentMatcher.normalize(text)

        if not text:
            return Intents.FALLBACK

        for intent, phrases in Intents.PHRASES.items():
            if any(phrase in text for phrase in phrases):
                return intent

        return Intents.FALLBACK

    @staticmethod
    def is_intent(text, intent):
        return IntentMatcher.detect(text) == intent


class Skill:
    def __init__(self, app):
        self.app = app

    def say(self, text):
        self.app.robot.say(text)

    def listen(self):
        return self.app.robot.listen()

    def gesture(self, name, intensity=1.0, duration=1.0, wait=True):
        self.app.robot.gesture(name, intensity=intensity, duration=duration, wait=wait)

    def detect_intent(self, text):
        return self.app.detect_intent(text)

    def increase_happiness(self, amount=0.1):
        self.app.increase_happiness(amount)

    def decrease_happiness(self, amount=0.1):
        self.app.decrease_happiness(amount)


class MemoryExercise(Skill):
    WORD_LIST = [
        "apple",
        "river",
        "jacket",
        "cat",
        "dog",
        "house",
        "car",
        "tree",
        "book",
        "phone",
        "table",
        "chair",
        "window",
        "door",
        "cup",
        "bottle",
        "pen",
        "paper",
        "shoe",
        "hat",
    ]

    def __init__(self, app):
        super().__init__(app)
        self.target_words = []
        self.said_words = set()

    def explain(self):
        self.say("Okay, let's do a daily exercise.")
        self.say("In this exercise, I will tell you three words. You need to remember them and repeat them back to me.")
        self.say("After the initial words, I may ask you again to check if you still remember them.")
        self.say("Okay?")

        user_text = self.listen()
        intent = self.detect_intent(user_text)

        if intent == Intents.AFFIRM:
            self.run()
        elif intent == Intents.REPEAT:
            self.say("No problem. I will tell you three words, and you should repeat them back to me.")
            self.say("Okay?")
            self.listen()
            self.run()
        else:
            self.say("I will start anyway. Try to remember the words.")
            self.run()

    def run(self):
        self.say("Great, let's start.")
        self.target_words = list(random.sample(self.WORD_LIST, 3))
        self.said_words = set()

        print(f"Chosen words are: {self.target_words}")

        words = self.target_words.copy()
        random.shuffle(words)

        self.say("Please remember these three words.")
        for word in words:
            self.say(word)

        while len(self.said_words) < len(self.target_words):
            self.say("Please repeat the words you remember.")
            user_text = self.listen()
            intent = self.detect_intent(user_text)

            if intent == Intents.UNKNOWN:
                self.decrease_happiness(0.1)
                self.say("Don't worry, it is okay to fail sometimes.")
                if self.confirm("Would you like to try again?"):
                    self.run()
                else:
                    self.say("Okay, we can stop here.")
                return

            if not user_text:
                self.decrease_happiness(0.1)
                self.say("That's okay. We can try again slowly.")
                continue

            self.check_words(user_text)

            if len(self.said_words) >= len(self.target_words):
                self.congratulate()
                return

            self.give_feedback(user_text)

    def check_words(self, user_text):
        for word in self.target_words:
            if word in user_text:
                self.said_words.add(word)

    def give_feedback(self, user_text):
        missing_count = len(self.target_words) - len(self.said_words)

        if len(self.said_words) >= 1:
            self.increase_happiness(0.05)
            self.say(f"Good. You remembered {len(self.said_words)} of them. There are just {missing_count} left.")
        else:
            self.decrease_happiness(0.1)
            self.say(f"I'm afraid {user_text} is not one of the words. Let's try again.")

    def confirm(self, question):
        self.say(question)
        user_text = self.listen()
        intent = self.detect_intent(user_text)

        if intent == Intents.AFFIRM:
            return True
        if intent == Intents.DENY:
            return False

        self.say("I will take that as yes.")
        return True

    def congratulate(self):
        self.increase_happiness(0.1)
        self.gesture("BigSmile", intensity=1.0, duration=3.0, wait=True)
        self.say("Congratulations. You remembered all three words.")
        self.say("That was very good.")

    def encourage(self):
        self.gesture("Smile", intensity=1.0, duration=2.0, wait=True)
        self.say("Don't worry, you can do it. Just try to remember one of the words at a time.")


class AgendaSkill(Skill):
    def run(self):
        self.say("Hmm, let me see.")
        self.say("Aha, I found it.")
        self.say("Based on what I know, it is probably time to feed the cat.")
        self.say("Would you like to do something else?")


class FurhatApp:
    def __init__(self):
        self.robot = FurhatRobot(ROBOT_IP, CHARACTER)
        self.user_happiness = STARTING_USER_HAPPINESS
        self.agenda_skill = AgendaSkill(self)
        self.memory_exercise = MemoryExercise(self)

    def detect_intent(self, text):
        return IntentMatcher.detect(text)

    def should_prompt_exercise(self):
        return self.user_happiness >= EXERCISE_HAPPINESS_THRESHOLD

    def increase_happiness(self, amount=0.1):
        self.user_happiness = min(1.0, self.user_happiness + amount)
        print(f"User happiness increased to: {self.user_happiness:.2f}")

    def decrease_happiness(self, amount=0.1):
        self.user_happiness = max(0.0, self.user_happiness - amount)
        print(f"User happiness decreased to: {self.user_happiness:.2f}")

    def start(self):
        self.robot.connect()
        try:
            self.robot.setup_face()
            self.robot.setup_listening()
            self.start_state()
        finally:
            self.robot.disconnect()

    def start_state(self):
        self.robot.say("Hello! You can ask me what is on your agenda today, or say let's do an exercise.")

        if self.should_prompt_exercise():
            self.robot.say("You seem to be doing well today.")
            self.robot.say("Would you like to do a short memory exercise?")
            user_text = self.robot.listen()
            intent = self.detect_intent(user_text)

            if intent == Intents.AFFIRM:
                self.memory_exercise.explain()
            elif intent == Intents.DENY:
                self.robot.say("No problem. We can do it later.")
            else:
                self.robot.say("That's okay. You can ask me for an exercise whenever you are ready.")

        while True:
            user_text = self.robot.listen()
            intent = self.detect_intent(user_text)

            if intent == Intents.FALLBACK and not user_text:
                self.robot.say("Hello? I am still listening.")

            elif intent == Intents.EXIT:
                self.robot.say("Okay, goodbye.")
                break

            elif intent == Intents.GREETING:
                self.robot.say("Hello. I am here with you.")

            elif intent == Intents.HELP:
                self.robot.say("You can ask about your agenda, or you can ask me to start an exercise.")

            elif intent == Intents.AGENDA:
                self.robot.gesture("BigSmile", intensity=1.0, duration=1.0, wait=True)
                self.agenda_skill.run()

            elif intent == Intents.EXERCISE:
                self.memory_exercise.explain()

            elif intent == Intents.REPEAT:
                self.robot.say("No problem. You can say agenda, exercise, help, or goodbye.")

            else:
                self.robot.say("I heard you, but I am not sure what you want me to do next.")
                self.robot.say("You can say agenda, exercise, help, or goodbye.")


if __name__ == "__main__":
    app = FurhatApp()
    app.start()