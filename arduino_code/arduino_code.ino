int pinRed = 2;
int pinWhite = 4;
int pinBuzzer = 6;

int currentStateRed = LOW, currentStateWhite = LOW;

int readingRed = 0, readingWhite = 0;
int debounceCountRed = 10, debounceCountWhite  = 10;
int counterRed = 0, counterWhite = 0;

long reading_time = 0;

void setup() {
  // put your setup code here, to run once:

  Serial.begin(9600);
  Serial.setTimeout(10);
  
  pinMode(pinRed, INPUT);
  pinMode(pinWhite, INPUT); 
  pinMode(pinBuzzer, OUTPUT);
  
}

void processCommand(String input) {
  input.trim(); // Remove any trailing newline or whitespace
  if (input.startsWith("buzz_")) {
    int firstUnderscore = input.indexOf('_');
    int secondUnderscore = input.indexOf('_', firstUnderscore + 1);

    String freqStr = input.substring(firstUnderscore + 1, secondUnderscore);
    String durStr = input.substring(secondUnderscore + 1);

    int frequency = freqStr.toInt();
    int duration = durStr.toInt();

    tone(pinBuzzer, frequency, duration);
  }
}

void loop() {

  if(Serial.available())
  {
    String str = Serial.readStringUntil('\n');
    processCommand(str);
  }


// If we have gone on to the next millisecond
  if(millis() != reading_time)
  {
    readingRed = digitalRead(pinRed);
    readingWhite = digitalRead(pinWhite);

    if(readingRed == currentStateRed && counterRed > 0){
      counterRed--;
    }
    else if(readingRed != currentStateRed){
      counterRed++;
    }

    if(readingWhite == currentStateWhite && counterWhite > 0){
      counterWhite--;
    }
    else if(readingWhite != currentStateWhite){
       counterWhite++;
    }

    // If any input has shown the same value for long enough, switch it
    if(counterRed >= debounceCountRed){
      counterRed = 0;
      currentStateRed = readingRed;
      if (currentStateRed == HIGH){
        Serial.println("red");
      }
    }

    if(counterWhite >= debounceCountWhite){
      counterWhite = 0;
      currentStateWhite = readingWhite;
      if (currentStateWhite == HIGH){
        Serial.println("white");
      }
    }
        
    reading_time = millis();}
}
