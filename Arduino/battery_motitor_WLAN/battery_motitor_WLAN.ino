#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

#include <Wire.h>

/*
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels
#define OLED_RESET     1 
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
*/

//#define RUN_ON_PC

#ifdef RUN_ON_PC
const char *ssid = "Fridolin"; // Your ssid
const char *password = "mein-esel-fridolin"; // Your Password
#else
const char *ssid = "Battery_Monitor"; // Your ssid
const char *password = "solaranlage"; // Your Password
#endif


IPAddress subnet(255, 255, 255, 0);			            // Subnet Mask
IPAddress gateway(192, 168, 2, 1);			            // Default Gateway

#ifdef RUN_ON_PC
IPAddress local_IP(192, 168, 1, 10);			        // Static IP Address for ESP8266
#else
IPAddress local_IP(192, 168, 2, 10);			        // Static IP Address for ESP8266
#endif

const uint16_t PORT = 1234;

#ifdef RUN_ON_PC
const char * SERVER_ADDRESS = "192.168.1.123";
#else
const char * SERVER_ADDRESS = "192.168.2.1";
#endif

/*void initDisplay()
{
  Serial.println("Initialze Display");
  Wire.begin(2,0);
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);

  Serial.print("Display: ");
  Serial.print(display.width());
  Serial.print("x");
  Serial.println(display.height());
  display.display();
  delay(2000); // Pause for 2 seconds  



  display.clearDisplay();
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.setTextColor(WHITE);
  display.display();

  display.drawLine(0, 0, display.width()-1, display.height()-1, SSD1306_WHITE);
  display.display();
}*/


void setup() {
  Serial.begin(115200);
 /* delay(10);

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
  Serial.println(WiFi.gatewayIP()); */


}

void loop() {
    WiFiClient client;

    if (!client.connect(SERVER_ADDRESS, PORT)) {

        Serial.println("Connection to host failed");

        delay(1000);
        return;
    }

    Serial.println("Connected to server successful!");

 /*   client.print("Hello from ESP32!");

    String answer = client.readString();
    Serial.println("Answer:" + answer);


    delay(1000);*/

    sendBatteryChargeCurrent(client, 3.4);

    Serial.println("Disconnecting...");
    client.stop();

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
  delay(3000);
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
