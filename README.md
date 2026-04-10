# 💊 Home Assistant Pill Logger
A highly advanced, fully local medication tracking and reminder integration for Home Assistant.  
Unlike simple counters, Pill Logger is a full-scale health management system. It calculates rolling time windows, warns against accidental overdoses, tracks inventory with self-resetting smart inputs, and powers actionable mobile reminders .

## ✨ Features
*   **Dynamic Scheduling:** Supports tracking medications via "Regular Interval" (e.g. every 8 hours), "Time of Day" (e.g. daily at 08:30), or purely "As Needed" .
*   **Safe Dose Tracking:** Set limits (e.g., "Max 2 pills per 8 hours"). The integration calculates your rolling window and tells you exactly how many safe doses you have left .
*   **Long-term Insights:** Automatically tracks your consumption patterns with rolling averages for 7 days, 30 days, and yearly (365 days). These sensors are smart enough to scale their calculations from the moment the medication is added or reset.
*   **Reconfigurable Settings:** Change your medication schedule, intervals, or safe dose limits at any time via the "Configure" button in the integration settings without needing to delete and recreate the entity.
*   **Smart Overdose Warning:** Dashboard UI dynamically swaps to a red warning button when safe doses reach 0, prompting an "Are you sure?" dialog before allowing an override .
*   **Smart Inventory:** Tracks your remaining pills. To refill, double-tap the inventory card, type the new box amount into the native Home Assistant text box, and it automatically adds it to your total and resets to 0 .
*   **Native Countdowns:** Outputs the exact `datetime` of your next available dose, allowing Home Assistant to natively show live-ticking countdowns like "Wait: 2 hours" or "Available now" .
*   **Built-in Reset:** Includes a dedicated configuration button to wipe a medication's history and start fresh without losing your current inventory counts .
*   **Blueprint Included:** Comes with a pre-built Blueprint for actionable mobile notifications (Take, Skip, Snooze) .

---

## 🛠️ Installation  

### 1. Install via HACS (Recommended)
1. Open HACS in your Home Assistant .
2. Click the 3 dots in the top right -> **Custom repositories** .
3. Paste the URL of this repository and select **Integration** as the category .
4. Click **Download** and restart Home Assistant .

### 2. Add your Medications
1. Go to **Settings > Devices & Services > Add Integration** .
2. Search for **Pill Logger** .
3. Follow the multi-step setup to define your medication (Regular Interval vs. Time of Day vs. As Needed, dosages, and current stock) .
4. Repeat this for as many medications as you need! All entities will be neatly grouped into a single Device per medication .

---

## 📱 The Dashboard (UI)  

To get a beautiful, app-like experience on your dashboard, you will need three popular frontend plugins installed via HACS:
* [Mushroom Cards](https://github.com/piitaya/lovelace-mushroom) 
* [Vertical Stack In Card](https://github.com/ofekashery/vertical-stack-in-card) 
* [Card-Mod](https://github.com/thomasloven/lovelace-card-mod) 

Once those are installed, add a "Manual" card to your dashboard and paste this code. *(Just do a Find & Replace for `YOUR_MEDICATION` to match your medication's entity name!)*  

**💡 How to refill:** Double-click the "Inventory Left" box to open the refill dialog, enter the new box amount, and close it to instantly add to your inventory .

```yaml
type: custom:vertical-stack-in-card
cards:
  - type: custom:mushroom-template-card
    entity: sensor.YOUR_MEDICATION_next_dose
    primary: YOUR_MEDICATION
    secondary: >-
      {% set next = states('sensor.YOUR_MEDICATION_next_dose') | as_datetime(None) %}
      {% if next == None or next <= now() %}
        Available now
      {% else %}
        {% set total_seconds = (next - now()).total_seconds() %}
        {% set hours = (total_seconds // 3600) | int %}
        {% set minutes = ((total_seconds % 3600) // 60) | int %}
        Wait: {% if hours > 0 %}{{ hours }} hours {% endif %}{{ minutes }} minutes
      {% endif %}
    card_mod:
      style: |
        ha-card {
          zoom: 1.2;
        }
  - type: horizontal-stack
    cards:
      - type: vertical-stack
        cards:
          - type: conditional
            conditions:
              - condition: numeric_state
                entity: sensor.YOUR_MEDICATION_safe_doses
                above: 0
            card:
              type: custom:mushroom-template-card
              primary: Take Pill
              secondary: |-
                {% if states('sensor.YOUR_MEDICATION_total_doses') | int(0) > 0 %}
                  {{ relative_time(states.sensor.YOUR_MEDICATION_total_doses.last_changed) }} ago
                {% else %}
                  Never ago
                {% endif %}
              icon: mdi:pill
              icon_color: blue
              layout: vertical
              tap_action:
                action: call-service
                service: button.press
                target:
                  entity_id: button.YOUR_MEDICATION_take_YOUR_MEDICATION
              card_mod:
                style: |
                  ha-card {
                    height: 120px !important;
                    display: flex;
                  ha-card:hover {
                    background: rgba(var(--rgb-blue), 0.1);
                    transition: background 0.2s ease;
                  }
                  ha-card:active {
                    transform: scale(0.95);
                    animation: pulse 0.3s ease;
                  }
                  @keyframes pulse {
                    0% { box-shadow: 0 0 0 0 rgba(var(--rgb-blue), 0.7); }
                    70% { box-shadow: 0 0 0 10px rgba(var(--rgb-blue), 0); }
                    100% { box-shadow: 0 0 0 0 rgba(var(--rgb-blue), 0); }
                  }
          - type: conditional
            conditions:
              - condition: state
                entity: sensor.YOUR_MEDICATION_safe_doses
                state: unknown
            card:
              type: custom:mushroom-template-card
              primary: Take Pill
              secondary: |-
                {% if states('sensor.YOUR_MEDICATION_total_doses') | int(0) > 0 %}
                  {{ relative_time(states.sensor.YOUR_MEDICATION_total_doses.last_changed) }} ago
                {% else %}
                  Never ago
                {% endif %}
              icon: mdi:pill
              icon_color: blue
              layout: vertical
              tap_action:
                action: call-service
                service: button.press
                target:
                  entity_id: button.YOUR_MEDICATION_take_YOUR_MEDICATION
              card_mod:
                style: |
                  ha-card {
                    height: 120px !important;
                    display: flex;
                  }
                  ha-card:hover {
                    background: rgba(var(--rgb-blue), 0.1);
                    transition: background 0.2s ease;
                  }
                  ha-card:active {
                    transform: scale(0.95);
                    animation: pulse 0.3s ease;
                  }
                  mushroom-shape-icon {
                    --icon-main-color: var(--rgb-blue) !important;
                    --icon-size: 40px !important;
                  }
                  @keyframes pulse {
                    0% { box-shadow: 0 0 0 0 rgba(var(--rgb-blue), 0.7); }
                    70% { box-shadow: 0 0 0 10px rgba(var(--rgb-blue), 0); }
                    100% { box-shadow: 0 0 0 0 rgba(var(--rgb-blue), 0); }
                  }
          - type: conditional
            conditions:
              - condition: numeric_state
                entity: sensor.YOUR_MEDICATION_safe_doses
                below: 1
            card:
              type: custom:mushroom-template-card
              primary: LIMIT REACHED
              secondary: |-
                {% if states('sensor.YOUR_MEDICATION_total_doses') | int(0) > 0 %}
                  {{ relative_time(states.sensor.YOUR_MEDICATION_total_doses.last_changed) }} ago
                {% else %}
                  Never ago
                {% endif %}
              icon: mdi:alert
              icon_color: red
              layout: vertical
              tap_action:
                action: call-service
                service: button.press
                target:
                  entity_id: button.YOUR_MEDICATION_take_YOUR_MEDICATION
                confirmation:
                  text: "WARNING: 0 safe doses available. Override?"
              card_mod:
                style: >
                  ha-card {
                    height: 120px !important;
                    display: flex;
                  }
                  
                  /* 1. Hide the native cropped icon entirely */
                  ha-state-icon {
                    display: none !important;
                  }
                  
                  /* 2. Draw a massive replacement icon AND circle using an un-croppable SVG overlay */
                  ha-card::after {
                    content: "";
                    position: absolute;
                    top: 0px; /* Adjust up/down to center in your layout */
                    left: 50%;
                    transform: translateX(-50%);
                    
                    /* Size of the Background Circle */
                    width: 70px; 
                    height: 70px;
                    
                    /* Inject the MDI Alert Icon (Material Red) */
                    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23F44336' d='M13 14H11V9H13M13 18H11V16H13M1 21H23L12 2L1 21Z'/%3E%3C/svg%3E");
                    background-repeat: no-repeat;
                    background-position: center;
                    
                    /* Size of the Warning Icon */
                    background-size: 50px 50px; 
                    
                    /* CRITICAL: Allows your mouse clicks to pass through to the button */
                    pointer-events: none; 
                  }

                  ha-card:hover {
                    background: rgba(var(--rgb-red), 0.1);
                  }

                  ha-card:active {
                    transform: scale(0.95);
                    animation: pulse-red 0.3s ease;
                  }

                  mushroom-shape-icon {
                    --icon-size: 60px !important;
                    --shape-color: rgba(var(--rgb-red), 0.2) !important;
                    --shape-outline-color: rgba(var(--rgb-red), 0.5) !important;
                  }

                  @keyframes pulse-red {
                    0% { box-shadow: 0 0 0 0 rgba(var(--rgb-red), 0.7); }
                    70% { box-shadow: 0 0 0 10px rgba(var(--rgb-red), 0); }
                    100% { box-shadow: 0 0 0 0 rgba(var(--rgb-red), 0); }
                  }
      - type: vertical-stack
        cards:
          - type: custom:mushroom-template-card
            entity: sensor.YOUR_MEDICATION_safe_doses
            primary: Can take
            secondary: "{{ states('sensor.YOUR_MEDICATION_safe_doses') }}"
            icon: mdi:pill
            icon_color: blue
            tap_action:
              action: none
          - type: custom:mushroom-template-card
            entity: number.YOUR_MEDICATION_pills_left
            primary: Left
            secondary: "{{ states('number.YOUR_MEDICATION_pills_left') }}"
            icon: mdi:pill
            icon_color: blue
            tap_action:
              action: none
            double_tap_action:
              action: more-info
              entity: number.YOUR_MEDICATION_add_YOUR_MEDICATION_refill
            card_mod:
              style: |
                ha-card:hover {
                  cursor: pointer;
                  background: rgba(var(--rgb-blue), 0.05);
                }
  - type: custom:mushroom-chips-card
    alignment: center
    chips:
      - type: template
        content: "7d Avg: {{ states('sensor.YOUR_MEDICATION_avg_daily_doses_7_days') }}"
        icon: mdi:chart-line
      - type: template
        content: "30d Avg: {{ states('sensor.YOUR_MEDICATION_avg_daily_doses_30_days') }}"
        icon: mdi:chart-line
      - type: template
        content: "Year Avg: {{ states('sensor.YOUR_MEDICATION_avg_daily_doses_yearly') }}"
        icon: mdi:chart-line

```

---

## ⏰ Smart Reminders (Blueprint)  
This repository includes a Blueprint that handles complex reminder loops. It sends an actionable notification to your phone. If you click "Take Now", it logs the pill natively. If you ignore it, it snoozes and loops .

**To install the Blueprint:**
1. Go to **Settings > Automations > Blueprints** .
2. Click **Import Blueprint** in the bottom right .
3. Paste the URL to the blueprint file in this repository:
`https://raw.githubusercontent.com/adix992/Home-Assistant-Pill-Logger/main/blueprints/reminder.yaml` 
4. Create a new automation using the blueprint, select your phone, and map your Pill Logger entities !

---
*Disclaimer: This integration is for informational and home automation purposes only. It is not a certified medical device. Always follow the advice of your doctor and the instructions on your prescription.* 
