#define trigPin 12          // define TrigPin
#define echoPin 11          // define EchoPin.
#define MAX_DISTANCE 200    // Maximum sensor distance is rated at 400-500cm.
#define TRIGGER_DISTANCE 30 // Distance threshold in cm to trigger PLAY command
// define the timeOut according to the maximum range. timeOut= 2*MAX_DISTANCE /100 /340 *1000000 = MAX_DISTANCE*58.8
float timeOut = MAX_DISTANCE * 60;
int soundVelocity = 340;    // define sound speed=340m/s
bool lastTriggered = false; // Track if we already triggered to avoid spam

void setup()
{
    pinMode(trigPin, OUTPUT); // set trigPin to output mode
    pinMode(echoPin, INPUT);  // set echoPin to input mode
    Serial.begin(9600);       // Open serial monitor at 9600 baud to see ping results.
}

void loop()
{
    delay(1000);                  // Wait 1s between pings. 29ms should be the shortest delay between pings.
    float distance = getSonar(); // Get distance in cm

    Serial.print("Distance: ");
    Serial.print(distance);
    Serial.println("cm");

    // Check if distance is below threshold and we haven't already triggered
    if (distance > 0 && distance <= TRIGGER_DISTANCE && !lastTriggered)
    {
        Serial.println("PLAY"); // Send PLAY command
        lastTriggered = true;
        Serial.print("Triggered at distance: ");
        Serial.print(distance);
        Serial.println("cm");
    }

    // Reset trigger state when object moves away (add some hysteresis)
    if (distance > TRIGGER_DISTANCE + 10 || distance == 0)
    {
        lastTriggered = false;
    }
}

float getSonar()
{
    unsigned long pingTime;
    float _distance;
    digitalWrite(trigPin, HIGH); // make trigPin output high level lasting for 10μs to triger HC_SR04,
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);
    pingTime = pulseIn(echoPin, HIGH, timeOut);             // Wait HC-SR04 returning to the high level and measure out this waitting time
    _distance = (float)pingTime * soundVelocity / 2 / 10000; // calculate the distance according to the time
    return _distance;                                        // return the distance value
}