#include "Arduino.h"
#include "Wire.h"
#include "DFRobot_VL53L0X.h"



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
long int flag = 0;
String receivedData;

DFRobot_VL53L0X sensor;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  sensor.begin(0x50);
  sensor.setMode(sensor.eContinuous,sensor.eHigh);
  sensor.start();
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

void loop() {

  Serial.println(distMeasure());
  if (Serial.available() > 0) {
    receivedData = Serial.readStringUntil('\n');
    flag = receivedData.toInt();
  }
  
  if(flag == 0){
    carStop();
  }
  else if(flag == 1){
    autoCar();
  }
  else if(flag == 2){
    manualCar();
  }
  else if(flag == 3){                 //"Smart" mode only uses the distance sensor for emergency braking
    smartCar();
  }
  
}

void smartCar(){
  while(receivedData != "q"){
    if(distMeasure() < 12.0 || sensor.getDistance() < 90.0){ 
      carStop();
      delay(1000);
      carBackwards();  
      delay(1000);
    }
    if(Serial.available() > 0) {
      receivedData = Serial.readStringUntil('\n');
    }
  }
}

void autoCar(){
  unsigned long currentMillis = millis();
  
    if(currentMillis - previousMillis >= interval){
      dist = distMeasure();
      previousMillis = currentMillis;
      resultsPrint(dist); 
    }

    if(sensor.getDistance() < 80){
      carStop();
    }
  
    if(dist > 24){
      carForwardVarSpeed(dist,5);
    } 
    else if(dist <= 24){
      unsigned long timeSinceTurning = millis();
      carStop();
      delay(500);
      if(LR_Flag == false){
        while((dist = distMeasure()) <= 24 || millis() - timeSinceTurning < 1500){          //millis returns the time the board has been running. SO it has to turn for, at least, one second
          carLeftTurn();
        }
        LR_Flag = !LR_Flag;
      }
      else{
        while((dist = distMeasure()) <= 24  || millis() - timeSinceTurning < 1500){
          carRightTurn();
        }
        LR_Flag = !LR_Flag;
      }
      carStop();
      delay(500);
    }
}

void manualCar(){
  setSpeedLow();
    while(true){
      
      if(sensor.getDistance() < 80){
        carStop();
        carBackwards();
        delay(500);
      }
      else{
        receivedData=Serial.readStringUntil('\n');
        if(receivedData == "c"){
          carStop();
          break;
        }
        if(receivedData == "f"){
          carForwardFixedSpeed();
        }
        else if(receivedData == "l"){
          carLeftTurn();
          delay(250);
        }
        else if(receivedData == "b"){
          carBackwards();
        }
        else if(receivedData == "r"){
          carRightTurn();
          delay(250);
        }
        else{
          carStop();
        }
      }
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
  if(dist >= 51){
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
  digitalWrite(bl1, HIGH);
  digitalWrite(bl2, LOW);
  digitalWrite(br1, LOW);
  digitalWrite(br2, HIGH);
  digitalWrite(fl1, LOW);
  digitalWrite(fl2, HIGH);
  digitalWrite(fr1, HIGH);
  digitalWrite(fr2, LOW); 
}

void carForwardFixedSpeed(){
  setSpeedLow();
  carForwardEnable();
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

void carLeftTurn(){
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

void carRightTurn(){
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
  analogWrite(benR, 120);
  analogWrite(benL, 120);
  analogWrite(fenR, 120);
  analogWrite(fenL, 120);  
}
