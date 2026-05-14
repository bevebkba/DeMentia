from furhat_realtime_api import FurhatClient
import logging
import random


ROBOT_IP = "127.0.0.1"
CHARACTER = "Titan (Adult)"
USER_HAPPINESS = 0.5


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
    MORNING_ROUTINE = "morning_routine"
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
        MORNING_ROUTINE: [
            "morning routine",
            "start morning routine",
            "start the morning routine",
            "begin morning routine",
            "wake up",
            "good morning",
            "start the demo",
            "demo",
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
                self.say("Don't worry, it is okay to fail sometimes.")
                if self.confirm("Would you like to try again?"):
                    self.run()
                else:
                    self.say("Okay, we can stop here.")
                return

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
            self.say(f"Good. You remembered {len(self.said_words)} of them. There are just {missing_count} left.")
        else:
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
        self.gesture("BigSmile", intensity=1.0, duration=3.0, wait=True)
        self.say("Congratulations. You remembered all three words.")
        self.say("That was very good.")

    def encourage(self):
        self.gesture("Smile", intensity=1.0, duration=2.0, wait=True)
        self.say("Don't worry, you can do it. Just try to remember one of the words at a time.")



class MorningRoutineSkill(Skill):
    def __init__(self, app):
        super().__init__(app)
        self.memory_words = ["apple", "river", "jacket"]

    def run(self):
        self.wake_up_scene()
        self.kitchen_scene()
        self.medication_scene()
        self.cognitive_exercise_scene()
        self.break_scene()
        self.memory_recall_scene()
        self.ending_scene()

    def wait_for_continue(self, fallback_text="Okay, let's continue."):
        user_text = self.listen()
        intent = self.detect_intent(user_text)

        if intent == Intents.REPEAT:
            self.say("No problem. I will repeat it.")
            return False
        if intent == Intents.DENY:
            self.say("That's okay. We can take it slowly.")
            return False

        self.say(fallback_text)
        return True

    def wake_up_scene(self):
        self.gesture("Smile", intensity=0.8, duration=2.0, wait=True)
        self.say("Good morning Arthur.")
        self.say("My name is Furhat, and I am your friend.")
        self.say("I will help you make your daily life easier.")
        self.say("If you don't mind, let's go to the kitchen.")
        self.wait_for_continue("Great. Let's go to the kitchen.")

    def kitchen_scene(self):
        self.say("Here we are in the kitchen.")
        self.say("Luna is probably hungry.")
        self.say("It is time to feed her.")
        self.say("The cat food is right there on the counter.")
        self.wait_for_continue("Well done.")

    def medication_scene(self):
        self.say("When you are ready, we will take your morning medication.")
        self.say("Please take your pill with a glass of water.")
        self.wait_for_continue("Good job, Arthur.")

    def cognitive_exercise_scene(self):
        self.say("Before breakfast, let's engage in an exercise to warm up your mind.")
        self.say("I will say three words. Try to remember them.")

        for word in self.memory_words:
            self.say(word)

        self.say("Now, let's try another exercise.")
        self.say("What goes with the word tree?")

        answer = self.listen()
        if "forest" in answer or "wood" in answer or "woods" in answer:
            self.gesture("BigSmile", intensity=1.0, duration=2.0, wait=True)
            self.say("Perfect. You are doing very well.")
        else:
            self.say("That's an interesting answer.")
            self.say("A common answer is forest.")
            self.say("You are doing well.")

    def break_scene(self):
        self.say("It's okay Arthur. Let's take a little break.")
        self.say("Let's go back to the living room.")
        self.wait_for_continue("Take your time. I am here with you.")
        self.say("I will show some old family pictures on the screen.")
        self.say("I will also play your favourite music.")

    def memory_recall_scene(self):
        self.say("Arthur, do you remember the three words from earlier?")
        answer = self.listen()

        remembered_words = []
        for word in self.memory_words:
            if word in answer:
                remembered_words.append(word)

        if len(remembered_words) == len(self.memory_words):
            self.gesture("BigSmile", intensity=1.0, duration=3.0, wait=True)
            self.say("Excellent. Your memory is strong today.")
        elif remembered_words:
            self.say(f"Good. You remembered {len(remembered_words)} words.")
            self.say("The three words were apple, river, and jacket.")
        else:
            self.say("That's okay. The words were apple, river, and jacket.")
            self.say("You still did a good job today.")

    def ending_scene(self):
        self.say("Now you can make your sandwich.")
        self.say("I will stay here calmly and help when you need me.")
        self.say("Calm reminders, simple conversations, and cognitive exercises can help you stay independent at home.")


class AgendaSkill(Skill):
    def run(self):
        self.say("Hmm, let me see.")
        self.say("Aha, I found it.")
        self.say("Based on what I know, it is probably time to feed Luna.")
        self.say("Would you like to start the morning routine?")


class FurhatApp:
    def __init__(self):
        self.robot = FurhatRobot(ROBOT_IP, CHARACTER)
        self.agenda_skill = AgendaSkill(self)
        self.memory_exercise = MemoryExercise(self)
        self.morning_routine = MorningRoutineSkill(self)

    def detect_intent(self, text):
        return IntentMatcher.detect(text)

    def start(self):
        self.robot.connect()
        try:
            self.robot.setup_face()
            self.robot.setup_listening()
            self.start_state()
        finally:
            self.robot.disconnect()

    def start_state(self):
        self.robot.say("Hello! You can say start the morning routine, ask what is on your agenda, or say let's do an exercise.")

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

            elif intent == Intents.MORNING_ROUTINE:
                self.morning_routine.run()

            elif intent == Intents.AGENDA:
                self.robot.gesture("BigSmile", intensity=1.0, duration=1.0, wait=True)
                self.agenda_skill.run()

            elif intent == Intents.EXERCISE:
                self.memory_exercise.explain()

            elif intent == Intents.REPEAT:
                self.robot.say("No problem. You can say morning routine, agenda, exercise, help, or goodbye.")

            else:
                self.robot.say("I heard you, but I am not sure what you want me to do next.")
                self.robot.say("You can say morning routine, agenda, exercise, help, or goodbye.")


if __name__ == "__main__":
    app = FurhatApp()
    app.start()