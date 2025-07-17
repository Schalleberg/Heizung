#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

#include <math.h>

#include <Wire.h>
#include "Adafruit_INA3221.h"
Adafruit_INA3221 ina3221;
#define INA3221_NUM_CHANNELS  3

#include "I2CScanner.h"
I2CScanner scanner;

#include "ArduinoJson.h"

typedef struct {
  float current[INA3221_NUM_CHANNELS];
  float voltage[INA3221_NUM_CHANNELS];

  void printVotageCurrent(int channel) {
    Serial.printf("Channel %u: voltage: %0.1f V current %0.2f A", channel, voltage[channel], current[channel]);
    Serial.println();
  }

  String serializeAsJson() {
    JsonDocument doc;
    String ret;
    doc["voltage"] = voltage[0];
    doc["current_0"] = current[0];
    serializeJson(doc,ret);
    return ret;
  }
} measurement_t;

#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels
#define OLED_RESET     -1 
Adafruit_SH1106G display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

#define RUN_ON_PC

#ifdef RUN_ON_PC
//const char *ssid = "Fridolin"; // Your ssid
//const char *password = "mein-esel-fridolin"; // Your Password
const char *ssid = "Oukitel";
const char *password = "fridolin1";
#else
const char *ssid = "Battery_Monitor"; // Your ssid
const char *password = "solaranlage"; // Your Password
#endif


IPAddress subnet(255, 255, 255, 0);			            // Subnet Mask
//IPAddress gateway(192, 168, 2, 1);			            // Default Gateway
IPAddress gateway(172, 19, 12, 163);			            // Default Gateway
const char* hostname = "ESP32";

#ifdef RUN_ON_PC
//IPAddress local_IP(192, 168, 1, 10);			        // Static IP Address for ESP8266
IPAddress local_IP(172, 19, 12, 50);			        // Static IP Address for ESP8266
#else
IPAddress local_IP(192, 168, 2, 10);			        // Static IP Address for ESP8266
#endif

const uint16_t PORT = 80;

#ifdef RUN_ON_PC
const char * SERVER_ADDRESS = "192.168.1.123";
#else
const char * SERVER_ADDRESS = "192.168.2.1";
#endif


WiFiServer server(PORT);

static float roundTo1Decimal(float value) {
  return round(value * 10.0) / 10.0;
}

void initDisplay() {
  Serial.printf("Initialze Display (heap %6d bytes)...\n", ESP.getFreeHeap());
  delay(250); // wait for the OLED to power up
  bool ret = display.begin(0x3C, true); // Address 0x3C default

  if(ret == false) {
    Serial.println("... failed");
    return;
  }
  Serial.println("... done");

  // Clear the buffer.
  display.clearDisplay();
  display.display();

}

void initINA3221(void){
  // Initialize the INA3221
  if (ina3221.begin(0x40, &Wire)) { // can use other I2C addresses or buses
    Serial.println("INA3221 Found!");
    ina3221.reset();
    ina3221.setAveragingMode(INA3221_AVG_16_SAMPLES);

    // Set shunt resistances for all channels
    ina3221.setShuntResistance(0, 0.005);
    ina3221.setShuntResistance(1, 0.1);
    ina3221.setShuntResistance(2, 0.1);

    ina3221.setPowerValidLimits(3.0 /* lower limit */, 15.0 /* upper limit */);
  } else {
    Serial.println("Failed to find INA3221 chip");
  }

}


void measureVoltageAndCurrents(measurement_t* pMeasurements)
{
  for (uint8_t i = 0; i < INA3221_NUM_CHANNELS; i++) {
    pMeasurements->current[i] = ina3221.getCurrentAmps(i);
    pMeasurements->voltage[i] = ina3221.getBusVoltage(i);   
  }

}

void displayMeasurements(measurement_t* pMeasurements)
{
  char txtBuffer[21];
  display.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, SH110X_BLACK);

  display.cp437(true);  // Use correct CP437 character codes
  display.setTextSize(3);
  display.setTextColor(SH110X_WHITE);

  int16_t x1=0, y1=0;
  uint16_t width=0, height=0;
  snprintf(txtBuffer, sizeof(txtBuffer), "%.1fV", roundTo1Decimal(pMeasurements->voltage[0]));
  display.getTextBounds(txtBuffer, 0, 0, &x1, &y1, &width, &height);
  display.setCursor((SCREEN_WIDTH - width) / 2, 0);
  display.print(txtBuffer);

  display.setTextSize(1);
  snprintf(txtBuffer, sizeof(txtBuffer), "%3.1fA %3.1fA %3.1fA",
                            roundTo1Decimal(pMeasurements->current[0]),
                            roundTo1Decimal(pMeasurements->current[1]),
                            roundTo1Decimal(pMeasurements->current[2]));
  display.getTextBounds(txtBuffer, 0, 0, &x1, &y1, &width, &height);
  display.setCursor((SCREEN_WIDTH - width) / 2, 30);
  display.print(txtBuffer);
  display.display();
}


void setup() {
  Serial.begin(115200);

  Wire.begin(2,0);
  scanner.Init();
  scanner.Scan();

  Serial.println("Initialize Display....");
  initDisplay();
  
  Serial.println("Initialize INA3221....");
  initINA3221();

  delay(10);

  WiFi.mode(WIFI_STA);
  WiFi.config(local_IP, gateway, subnet);//, primaryDNS, secondaryDNS);
  WiFi.hostname(hostname);
  WiFi.begin(ssid, password);
/*  if (WiFi.waitForConnectResult() != WL_CONNECTED) {
    Serial.println("WiFi Failed!");
    while(true) yield();
  }*/



/*
  if (WiFi.config(local_IP, gateway, subnet)) {
    Serial.println("Static IP Configured");
  }
  else {
    Serial.println("Static IP Configuration Failed");
  }

  // Connect to WiFi network
  Serial.println();
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);
*/
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  
  Serial.println("");
  Serial.println("WiFi connected");

  // Print the IP address
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  Serial.print("GATEWAY: ");
  Serial.println(WiFi.gatewayIP());

  server.begin();

}

unsigned long ms = 0;
String strReq;
void loop() {
  measurement_t measurements;
  if (millis() - ms > 2000 || ms == 0)
  {
      ms = millis();
      measureVoltageAndCurrents(&measurements);
      measurements.printVotageCurrent(0);
      displayMeasurements(&measurements);
  }

  if (WiFi.status() == WL_CONNECTED) {
    // listen for incoming clients
    WiFiClient client = server.accept();
    
    if (client == true) {
      Serial.println("Client connected.");
      Serial.print("Available bytes: ");
      Serial.println(client.available());
      strReq = client.readString();
      
      size_t lenRequest = strReq.length();

      if (lenRequest > 0) {
        
        char* request = (char*)malloc(lenRequest + 1);
        strReq.toCharArray(request,lenRequest + 1);
        Serial.print("Request:");
        Serial.println(request);

        // parse request
        const char* method = strtok(request, " \n\r");
        const char* uri = strtok(NULL, " \n\r");
        const char* httpVersion = strtok(NULL, " \n\r");
        Serial.println(method);
        Serial.println(uri);
        Serial.println(httpVersion);
        

        if (strcmp(method,"GET") == 0) {
          String strUri(uri);
          
          if (strUri.startsWith("/?measurements")) {
            String response("HTTP/1.1 200 OK\r\n");
            //response += "Content-Type: application/json\r\n";
            response += "Content-Type: text/html\r\n";
            response += "\r\n";
            response += "<HTML>\r\n";
            response += measurements.serializeAsJson();
            response += "</HTML>";
            Serial.println("Response:");
            Serial.println(response);
            client.println(response);
          } else {
            Serial.println("Unknown URI");
            client.println("HTTP/1.1 400 	Bad Request");
            client.println();
          }
        } else {
            Serial.println("Method not supported");
            client.println("HTTP/1.1 400 	Bad Request");
            client.println();
        }
        free(request);
        client.stop();
      }
    }
  }


/*

    WiFiClient client;

    if (!client.connect(SERVER_ADDRESS, PORT)) {

        Serial.println("Connection to host failed");

        delay(1000);
        return;
    }

    Serial.println("Connected to server successful!");

    client.print("Hello from ESP32!");

    String answer = client.readString();
    Serial.println("Answer:" + answer);


    delay(1000);

   

    sendBatteryChargeCurrent(client, 3.4);

    Serial.println("Disconnecting...");
    client.stop();

*/
//WiFiClient client = server.available();
//client.println("HTTP/1.1 200 OK");
//client.println("Content-Type: text/html");
//client.println("Connection: close");  // the connection will be closed after completion of the response
//client.println("Refresh: 5");  // refresh the page automatically every 5 sec
//client.println();
//client.println("<!DOCTYPE HTML>");
//client.println("<html>");
//client.print("<p style='text-align: center;'>&nbsp;</p>");
//client.print("<p style='text-align: center;'><span style='font-size: x-large;'><strong>ESP8266 and DS18B20 Temperature Sensor Server</strong></span></p>");
//client.print("<p style='text-align: center;'><span style='font-size: x-large;'><strong>www.elec-cafe.com</strong></span></p>");
//client.print("<p style='text-align: center;'><span style='color: #0000ff;'><strong style='font-size: large;'>Temperature = ");
//client.println(celsius);
//
//client.print("<p style='text-align: center;'><span style='color: #0000ff;'><strong style='font-size: large;'>Switch = ");
//client.println(switchVal);
//
//client.print("<p style='text-align: center;'>&nbsp;</p>");
//client.print("<p style='text-align: center;'>&nbsp;</p>");
//client.print("<p style='text-align: center;'>&nbsp;");
//client.print("</p>");
//client.println("</html>");
 delay(10);
}


void sendBatteryChargeCurrent(WiFiClient client, float value) {
    HTTPClient http;
    http.begin(client, SERVER_ADDRESS + String("battery_charge_current"));
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");

    String postData = "current=" + String(value, 1);;  

    Serial.println("Send: " + http.getString());

    int httpResponseCode = http.POST(postData);  

    if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.println("Antwort: " + response);
    } else {
        Serial.println("Fehler: " + String(httpResponseCode));
    }

    http.end();
}
