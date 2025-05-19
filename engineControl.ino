const int echoPin = 12;
const int triggerPin = 13;
const int benR = 6, benL = 6, fenR = 6, fenL = 6; //Back/Front enable Right/Left -> For speed control
float dist = 0, duration;
int bl1 = 2, bl2 = 3, br1 = 4, br2 = 5;   //back, left/right, in1/2
int fr1 = 8, fr2 = 9, fl1 = 10, fl2 = 11;   //front, left/right, in1/2
bool LR_Flag = false;
int last_state = 0;
unsigned long previousMillis = 0;         //To store the last time we had a reading
const long interval = 100;                //10 measurements per second

void setup() {
  Serial.begin(9600);
  pinMode(triggerPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(bl1, OUTPUT);
  pinMode(bl2, OUTPUT);
  pinMode(br1, OUTPUT);
  pinMode(br2, OUTPUT);
  pinMode(fl1, OUTPUT);
  pinMode(fl2, OUTPUT);
  pinMode(fr1, OUTPUT);
  pinMode(fr2, OUTPUT);
  pinMode(benR, OUTPUT);
  pinMode(benL, OUTPUT);
  pinMode(fenR, OUTPUT);
  pinMode(fenL, OUTPUT);
}

/*
You could make the speed of the car totally dependent of the distance, instead of using if clauses Ex: 
  void setSpeed(float dist){
    if(dist < 15) carStop();
    else{
      speed = dist*0.5;
      analogWrite(benR, speed);
    }
  }
*/
/*


/*Do another if, when it's really close, so that the car goes backweards to increase its distance to an obstacle and then, does a right, or left turn;*/
void loop() {
  
  unsigned long currentMillis = millis();
  
  if(currentMillis - previousMillis >= interval){
    dist = distMeasure();
    previousMillis = currentMillis;
    resultsPrint(dist); 
  }
  
  if(dist > 14){
    carForwardVarSpeed(dist,7);
  } 
  else if(dist <= 14){
    carStop();
    delay(500);
    if(LR_Flag == false){
      while((dist = distMeasure()) <= 14){
        carLeftTurn();
      }
      LR_Flag = !LR_Flag;
    }
    else{
      while((dist = distMeasure()) <= 14){
        carRightTurn();
      }
      LR_Flag = !LR_Flag;
    }
    carStop();
    delay(500);
  }
  
}


float distMeasure(){
  digitalWrite(triggerPin, LOW);
  delayMicroseconds(10);
  digitalWrite(triggerPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(triggerPin, LOW);
  delayMicroseconds(2);

  duration = pulseIn(echoPin, HIGH);     //Measures the time the echo pin takes to recieve a "HIGH" input;
  
  return (duration*0.0343)/2;  
}

void resultsPrint(float dist){
  Serial.print("Distance: ");
  Serial.println(dist);
}

// ---------- Functions for forward motion ----------
void carForwardVarSpeed(float dist, int k){
  carForwardEnable();
  if(dist >= 36){
    analogWrite(benR, 255);
    analogWrite(benL, 255);
    analogWrite(fenR, 255);
    analogWrite(fenL, 255);
  }else{
    analogWrite(benR, dist*k);
    analogWrite(benL, dist*k);
    analogWrite(fenR, dist*k);
    analogWrite(fenL, dist*k);
  }
}

void carForwardEnable(){        //Func just to set the driver pins for the car to go forward
  digitalWrite(bl1, LOW);
  digitalWrite(bl2, HIGH);
  digitalWrite(br1, HIGH);
  digitalWrite(br2, LOW);
  digitalWrite(fl1, HIGH);
  digitalWrite(fl2, LOW);
  digitalWrite(fr1, LOW);
  digitalWrite(fr2, HIGH);  
}


// ---------- Functions for turning, stopping and going backwards ----------
void carBackwards(){
  setSpeedLow();
  digitalWrite(bl1, LOW);
  digitalWrite(bl2, HIGH);
  digitalWrite(br1, LOW);
  digitalWrite(br2, HIGH);
  digitalWrite(fl1, LOW);
  digitalWrite(fl2, HIGH);
  digitalWrite(fr1, LOW);
  digitalWrite(fr2, HIGH); 
}

void carStop(){
  digitalWrite(bl1, LOW);
  digitalWrite(bl2, LOW);
  digitalWrite(br1, LOW);
  digitalWrite(br2, LOW);
  digitalWrite(fl1, LOW);
  digitalWrite(fl2, LOW);
  digitalWrite(fr1, LOW);
  digitalWrite(fr2, LOW);
}

void carRightTurn(){
  setSpeedLow();
  digitalWrite(bl1, LOW);
  digitalWrite(bl2, HIGH);
  digitalWrite(br1, LOW);
  digitalWrite(br2, HIGH);
  digitalWrite(fl1, HIGH);
  digitalWrite(fl2, LOW);
  digitalWrite(fr1, HIGH);
  digitalWrite(fr2, LOW);
}

void carLeftTurn(){
  setSpeedLow();
  digitalWrite(bl1, HIGH);
  digitalWrite(bl2, LOW);
  digitalWrite(br1, HIGH);
  digitalWrite(br2, LOW);
  digitalWrite(fl1, LOW);
  digitalWrite(fl2, HIGH);
  digitalWrite(fr1, LOW);
  digitalWrite(fr2, HIGH);
}

void setSpeedLow(){
  analogWrite(benR, 90);
  analogWrite(benL, 90);
  analogWrite(fenR, 90);
  analogWrite(fenL, 90);  
}
