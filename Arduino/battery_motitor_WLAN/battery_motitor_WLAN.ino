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


//#define USE_SOFT_AP

#ifdef USE_SOFT_AP
const char *ssid = "Battery_Monitor";
const char *password = "solaranlage";

IPAddress local_IP(192, 168, 2, 1);
IPAddress subnet(255, 255, 255, 0);
IPAddress gateway(192, 168, 2, 1);
#else
//const char *ssid = "Fridolin"; // Your ssid
//const char *password = "mein-esel-fridolin"; // Your Password
const char *ssid = "Oukitel";
const char *password = "fridolin1";

IPAddress subnet(255, 255, 255, 0);
IPAddress gateway(172, 19, 12, 163);			            // Default Gateway
const char* hostname = "ESP32";
//IPAddress local_IP(192, 168, 1, 10);
IPAddress local_IP(172, 19, 12, 50);

WiFiEventHandler gotIpEventHandler, disconnectedEventHandler;
#endif

const uint16_t PORT = 80;

const uint32_t MEASUREMENT_INTERVAL_MS= 2000;

WiFiServer server(PORT);
measurement_t measurements;

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

void displayValues()
{
  char txtBuffer[21];
  display.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, SH110X_BLACK);

  display.cp437(true);  // Use correct CP437 character codes
  display.setTextSize(3);
  display.setTextColor(SH110X_WHITE);

  int16_t x1=0, y1=0;
  uint16_t width=0, height=0;

  // display voltage
  snprintf(txtBuffer, sizeof(txtBuffer), "%.1fV", roundTo1Decimal(measurements.voltage[0]));
  display.getTextBounds(txtBuffer, 0, 0, &x1, &y1, &width, &height);
  display.setCursor((SCREEN_WIDTH - width) / 2, 0);
  display.print(txtBuffer);

  // display currents
  display.setTextSize(1);
  snprintf(txtBuffer, sizeof(txtBuffer), "%3.1fA %3.1fA %3.1fA",
                            roundTo1Decimal(measurements.current[0]),
                            roundTo1Decimal(measurements.current[1]),
                            roundTo1Decimal(measurements.current[2]));
  display.getTextBounds(txtBuffer, 0, 0, &x1, &y1, &width, &height);
  display.setCursor((SCREEN_WIDTH - width) / 2, 30);
  display.print(txtBuffer);

  // show status
  display.setTextSize(1);
  #ifdef USE_SOFT_AP
  snprintf(txtBuffer, sizeof(txtBuffer), "IP: %s N=%u", WiFi.softAPIP().toString().c_str(), WiFi.softAPgetStationNum());
  #else
  if (WiFi.status() == WL_CONNECTED) {
    snprintf(txtBuffer, sizeof(txtBuffer), "IP: %s", WiFi.localIP().toString().c_str());
  } else {
    snprintf(txtBuffer, sizeof(txtBuffer), "IP: disconnected");
  }
  #endif

  display.getTextBounds(txtBuffer, 0, 0, &x1, &y1, &width, &height);
  display.setCursor((SCREEN_WIDTH - width) / 2, 50);
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

#ifdef USE_SOFT_AP
  // setupWiFi AP
  Serial.print("Setup Soft-AP: ");
  WiFi.onSoftAPModeStationConnected([](const WiFiEventSoftAPModeStationConnected& event)
  {
    Serial.println("WIFI onSoftAPModeStationConnected");
  });

  WiFi.onWiFiModeChange([](const WiFiEventModeChange& event)
  {
    Serial.println("WIFI onWiFiModeChange");
  });

  if(WiFi.softAPConfig(local_IP, gateway, subnet))
  {
    Serial.println("successful");
  } else {
    Serial.println("failed");
  }

  //WiFi.hostname(hostname);
  Serial.print("Start Soft-AP: ");
  if(WiFi.softAP(ssid, password, 1, false, 2))
    {
    Serial.print("successful.");
    Serial.print("IP: ");
    Serial.println(WiFi.softAPIP());

  } else {
    Serial.println("failed");
  }
  Serial.println(WiFi.localIP());

#else
  WiFi.mode(WIFI_STA);
  WiFi.config(local_IP, gateway, subnet);
  WiFi.hostname(hostname);

  gotIpEventHandler = WiFi.onStationModeGotIP([](const WiFiEventStationModeGotIP& event)
  {
    Serial.print("WIFI connected, IP: ");
    Serial.println(WiFi.localIP());
  });

  disconnectedEventHandler = WiFi.onStationModeDisconnected([](const WiFiEventStationModeDisconnected& event)
  {
    Serial.println("WIFI disconnected");
  });

  WiFi.begin(ssid, password);
  #endif

  server.begin();
}



unsigned long ms = 0;
void loop() {
  
  if (millis() - ms > MEASUREMENT_INTERVAL_MS || ms == 0)
  {
      ms = millis();
      measureVoltageAndCurrents(&measurements);
      measurements.printVotageCurrent(0);
  }

#ifdef USE_SOFT_AP
  if (WiFi.softAPgetStationNum() > 0) {
#else
  if (WiFi.status() == WL_CONNECTED) {
#endif
    // listen for incoming clients
    WiFiClient client = server.accept();

    if (client == true) {
      String strReq;
      Serial.println("Client connected.");

      client.setTimeout(500);

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

        if (strcmp(method,"GET") == 0) {
          if (strcmp(uri, "/?measurements") == 0) {
            String response("HTTP/1.1 200 OK\r\n");
            response += "Content-Type: application/json\r\n";
            response += "\r\n";
            response += measurements.serializeAsJson();
            client.println(response);
          } else {
            Serial.println();
            client.println("HTTP/1.1 400 	Bad Request\r\n");
            client.println();
            client.println("Unknown URI\r\n");
          }
        } else {
            Serial.println("");
            client.println("HTTP/1.1 400 	Bad Request\r\n");
            client.println();
            client.println("Method not supported\r\n");
        }
        free(request);
        client.stop();
      }
    }
  }

  displayValues();


 delay(100);
}

