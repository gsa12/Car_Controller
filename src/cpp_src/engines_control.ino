#include "Arduino.h"
#include "Wire.h"

const int echoPin = 12;
const int triggerPin = 13;
const int benR = 6, benL = 6, fenR = 6, fenL = 6; //Back/Front enable Right/Left -> For speed control
const int left_light = A3, right_light = A2;
float dist = 0, duration;
int bl1 = 2, bl2 = 3, br1 = 4, br2 = 5;   //back, left/right, in1/2
int fr1 = 8, fr2 = 9, fl1 = 10, fl2 = 11;   //front, left/right, in1/2
bool LR_Flag = false;
int last_state = 0;
unsigned long previousMillis = 0;         //To store the last time we had a reading
const long interval = 100;                //10 measurements per second
long int flag = 0;
String receivedData, currentCommand = "", previousCommand = "";

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
    pinMode(left_light, OUTPUT);
    pinMode(right_light, OUTPUT);
    pinMode(LED_BUILTIN, OUTPUT);
}

//void loop(){
//  //manualCar();
//  //Serial.println(distMeasure());
//  //Serial.println(sensor.getDistance());
//  //delay(500);
//  autoCar();
//}

void loop() {
    digitalWrite(LED_BUILTIN, HIGH);
    if (Serial.available() > 0) {
        receivedData = Serial.readStringUntil('\n');
        flag = receivedData.toInt();
    }

    if (flag == 0) {
        carStop();
    }
    else if (flag == 1) {
        autoCar();
    }
    else if (flag == 2) {
        manualCar();
    }
    else {
        carStop();
    }
}

void autoCar() {
    unsigned long currentMillis = millis();
    digitalWrite(LED_BUILTIN, LOW);
    while (true) {

        if (Serial.available() > 0) {
            receivedData = Serial.readStringUntil('\n');
            if (receivedData == "STOP") {
                carStop();
                flag = 0;
                break;
            }
        }

        dist = distMeasure();
        if (dist > 24) {
            carForwardVarSpeed(dist, 4);
        }
        else if (dist <= 24) {
            unsigned long timeSinceTurning = millis();
            carStop();
            delay(500);
            if (LR_Flag == false) {
                digitalWrite(right_light, LOW);
                digitalWrite(left_light, HIGH);
                while ((dist = distMeasure()) <= 24 || millis() - timeSinceTurning < 1500) {          //millis returns the time the board has been running. SO it has to turn for, at least, one second
                    carLeftTurn();
                }
                LR_Flag = !LR_Flag;
                digitalWrite(left_light, LOW);
            }
            else {
                digitalWrite(right_light, HIGH);
                digitalWrite(left_light, LOW);
                while ((dist = distMeasure()) <= 24 || millis() - timeSinceTurning < 1500) {
                    carRightTurn();
                }
                LR_Flag = !LR_Flag;
                digitalWrite(left_light, LOW);
            }
            carStop();
            digitalWrite(right_light, HIGH);
            digitalWrite(left_light, HIGH);
            delay(500);
        }

    }
}

void manualCar() {
    setSpeedLow();
    digitalWrite(LED_BUILTIN, LOW);
    unsigned long lastCommandTime;
    const unsigned long timeout = 100;
    while (true) {
        if (distMeasure() < 15.0) {
            digitalWrite(right_light, HIGH);
            digitalWrite(left_light, HIGH);
            while (distMeasure() < 15.0) {
                carStop();
                delay(500);
                carBackwards();
                delay(300);
            }
            carStop();
            delay(200);
            digitalWrite(right_light, LOW);
            digitalWrite(left_light, LOW);
        }
        else {
            if (Serial.available() > 0) {
                receivedData = Serial.readStringUntil('\n');
                if (receivedData == "c" || receivedData == "STOP") {
                    carStop();
                    flag = 0;
                    currentCommand = "";
                    previousCommand = "";
                    digitalWrite(left_light, LOW);
                    digitalWrite(right_light, LOW);
                    break;
                }

                lastCommandTime = millis();
                previousCommand = currentCommand;
                currentCommand = receivedData;
            }
            if(millis() - lastCommandTime > timeout){
                currentCommand = "";
            }

            if (previousCommand != currentCommand) {
                digitalWrite(left_light, LOW);
                digitalWrite(right_light, LOW);
                if (currentCommand == "l") digitalWrite(right_light, HIGH);
                if (currentCommand == "r") digitalWrite(left_light, HIGH);
            }

            if (currentCommand == "f") {
                carForwardFixedSpeed();
            }
            else if (currentCommand == "l") {
                carLeftTurn();
            }
            else if (currentCommand == "b") {
                carBackwards();
            }
            else if (currentCommand == "r") {
                carRightTurn();
            }
            else {
                carStop();
            }
        }
    }
}

float distMeasure() {
    digitalWrite(triggerPin, LOW);
    delayMicroseconds(10);
    digitalWrite(triggerPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(triggerPin, LOW);
    delayMicroseconds(2);

    duration = pulseIn(echoPin, HIGH);     //Measures the time the echo pin takes to recieve a "HIGH" input;

    return (duration * 0.0343) / 2;
}

void resultsPrint(float dist) {
    Serial.print("Distance: ");
    Serial.println(dist);
}

// ---------- Functions for forward motion ----------
void carForwardVarSpeed(float dist, int k) {
    carForwardEnable();
    if (dist >= 51) {
        analogWrite(benR, 255);
        analogWrite(benL, 255);
        analogWrite(fenR, 255);
        analogWrite(fenL, 255);
    } else {
        analogWrite(benR, dist * k);
        analogWrite(benL, dist * k);
        analogWrite(fenR, dist * k);
        analogWrite(fenL, dist * k);
    }
}

void carForwardEnable() {        //Func just to set the driver pins for the car to go forward
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
void carBackwards() {
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

void carForwardFixedSpeed() {
    setSpeedLow();
    carForwardEnable();
}

void carStop() {
    digitalWrite(LED_BUILTIN, LOW);
    digitalWrite(bl1, LOW);
    digitalWrite(bl2, LOW);
    digitalWrite(br1, LOW);
    digitalWrite(br2, LOW);
    digitalWrite(fl1, LOW);
    digitalWrite(fl2, LOW);
    digitalWrite(fr1, LOW);
    digitalWrite(fr2, LOW);
}

void carLeftTurn() {
    setSpeedLowTurns();
    digitalWrite(bl1, LOW);
    digitalWrite(bl2, HIGH);
    digitalWrite(br1, LOW);
    digitalWrite(br2, HIGH);
    digitalWrite(fl1, HIGH);
    digitalWrite(fl2, LOW);
    digitalWrite(fr1, HIGH);
    digitalWrite(fr2, LOW);
}

void carRightTurn() {
    setSpeedLowTurns();
    digitalWrite(bl1, HIGH);
    digitalWrite(bl2, LOW);
    digitalWrite(br1, HIGH);
    digitalWrite(br2, LOW);
    digitalWrite(fl1, LOW);
    digitalWrite(fl2, HIGH);
    digitalWrite(fr1, LOW);
    digitalWrite(fr2, HIGH);
}

void setSpeedLow() {
    analogWrite(benR, 110);
    analogWrite(benL, 110);
    analogWrite(fenR, 110);
    analogWrite(fenL, 110);
}

void setSpeedLowTurns() {
    analogWrite(benR, 140);
    analogWrite(benL, 140);
    analogWrite(fenR, 140);
    analogWrite(fenL, 140);
}