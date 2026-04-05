
# 💊 Home Assistant Pill Logger

A highly advanced, fully local medication tracking and reminder integration for Home Assistant. 

Unlike simple counters, Pill Logger is a full-scale health management system. It calculates rolling time windows, prevents accidental overdoses, tracks inventory with self-resetting smart inputs, and powers actionable mobile reminders.

## ✨ Features
* **Safe Dose Tracking:** Set limits (e.g., "Max 2 pills per 8 hours"). The integration calculates your rolling window and tells you exactly how many safe doses you have left.
* **Overdose Blocker:** If you try to log a pill when you have 0 safe doses available, the integration blocks the action and throws a UI error.
* **Smart Inventory:** Tracks your remaining pills. To refill, just type the new box amount into the native Home Assistant text box, and it automatically adds it to your total and resets to 0.
* **Native Countdowns:** Outputs the exact `datetime` of your next available dose, allowing Home Assistant to natively show "Wait: 2 hours" or "Available now".
* **Blueprint Included:** Comes with a pre-built Blueprint for actionable mobile notifications (Take, Skip, Snooze).

---

## 🛠️ Installation

### 1. Install via HACS (Recommended)
1. Open HACS in your Home Assistant.
2. Click the 3 dots in the top right -> **Custom repositories**.
3. Paste the URL of this repository and select **Integration** as the category.
4. Click **Download** and restart Home Assistant.

### 2. Add your Medications
1. Go to **Settings > Devices & Services > Add Integration**.
2. Search for **Pill Logger**.
3. Follow the multi-step setup to define your medication (Regular Interval vs. As Needed, dosages, and current stock).
4. Repeat this for as many medications as you need!

---

## 📱 The Dashboard (UI)

To get a beautiful, app-like experience on your dashboard, you will need two popular frontend plugins installed via HACS:
* [Mushroom Cards](https://github.com/piitaya/lovelace-mushroom)
* [Vertical Stack In Card](https://github.com/ofekashery/vertical-stack-in-card)

Once those are installed, add a "Manual" card to your dashboard and paste this code. *(Just do a Find & Replace for `YOUR_MEDICATION` to match your medication's entity names!)*
How to refill: Double click inventory to open the refill dialouge, enter a number and close it again to refill

```yaml
type: custom:vertical-stack-in-card
cards:
  # 1. The Header 
  - type: custom:mushroom-template-card
    entity: sensor.YOUR_MEDICATION_next_dose
    primary: YOUR_MEDICATION
    secondary: >-
      {% set next = states('sensor.YOUR_MEDICATION_next_dose') %}
      {% if next in ['unknown', 'unavailable', 'None', ''] %}
        Available now
      {% elif next | as_datetime(None) != None and now() < next | as_datetime %}
        Wait: {{ next | as_datetime | time_until(now()) }}
      {% else %}
        Available now
      {% endif %}
    icon: mdi:medical-bag
    icon_color: blue
    badge_icon: >-
      {% if states('sensor.YOUR_MEDICATION_safe_doses') | int(0) > 0 %}
        mdi:check
      {% else %}
        mdi:clock-outline
      {% endif %}
    badge_color: >-
      {% if states('sensor.YOUR_MEDICATION_safe_doses') | int(0) > 0 %}
        green
      {% else %}
        orange
      {% endif %}
      
  # 2. The Interactive Buttons
  - type: horizontal-stack
    cards:
      # --- BUTTON STATE A: Safe to take ---
      - type: conditional
        conditions:
          - condition: numeric_state
            entity: sensor.YOUR_MEDICATION_safe_doses
            above: 0
        card:
          type: custom:mushroom-entity-card
          entity: button.take_YOUR_MEDICATION
          name: Take Pill
          layout: vertical
          icon_color: blue
          show_state: false
          tap_action:
            action: call-service
            service: button.press
            target:
              entity_id: button.take_YOUR_MEDICATION
              
      # --- BUTTON STATE B: 0 Doses Left (WARNING!) ---
      - type: conditional
        conditions:
          - condition: numeric_state
            entity: sensor.YOUR_MEDICATION_safe_doses
            below: 1
        card:
          type: custom:mushroom-entity-card
          entity: button.take_YOUR_MEDICATION
          name: LIMIT REACHED
          layout: vertical
          icon_color: red
          icon: mdi:alert
          show_state: false
          tap_action:
            action: call-service
            service: button.press
            target:
              entity_id: button.take_YOUR_MEDICATION
            confirmation:
              text: "WARNING: You have 0 safe doses available. Are you sure you want to take this pill anyway?"
              
      # --- The Stats ---
      - type: custom:mushroom-entity-card
        entity: sensor.YOUR_MEDICATION_safe_doses
        name: Safe Doses
        layout: vertical
        
      # --- Hidden Refill Input (Disguised as Inventory) ---
      - type: custom:mushroom-template-card
        entity: number.add_YOUR_MEDICATION_refill
        primary: Inventory Left
        secondary: "{{ states('number.YOUR_MEDICATION_pills_left') }}"
        icon: mdi:medical-bag
        layout: vertical
        tap_action:
          action: none
        double_tap_action:
          action: more-info
```

---

## ⏰ Smart Reminders (Blueprint)

This repository includes a Blueprint that handles complex reminder loops. It sends an actionable notification to your phone. If you click "Take", it logs the pill natively. If you ignore it, it snoozes and loops.

**To install the Blueprint:**
1. Go to **Settings > Automations > Blueprints**.
2. Click **Import Blueprint** in the bottom right.
3. Paste the URL to the blueprint file in this repository:
   `https://raw.githubusercontent.com/YOUR_GITHUB_NAME/Home-Assistant-Pill-Logger/main/blueprints/reminder.yaml`
4. Create a new automation using the blueprint, select your phone, and map your Pill Logger entities!

---
*Disclaimer: This integration is for informational and home automation purposes only. It is not a certified medical device. Always follow the advice of your doctor and the instructions on your prescription.*
