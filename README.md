# SimDoctor 

An AI vehicle doctor. It watches a live sensor feed, catches the fault, and explains what 
to check, with every answer grounded in MongoDB Atlas.

Built at Encode London 2026 for the MongoDB Atlas: Build Anything, Change Everything challenge.

---------> screenshot or GIF of the dashboard goes here <-----------

The problem

A warning light comes on and most drivers have no idea what it means, how serious it is, or whether 
it is safe to keep driving. Diagnostic tools give you a code. They don't give you a plain-English answer
you can trust!!

## What SimDoctor does 
1. Streams a live drive.Sensor readings(engine temperature, battery voltage, oil pressure, speed, RPM) arrive one at a time and are written to Atlas as they arrive.
2. Catches faults in real time. A rule-based doctor flags readings that cross a limit, and the dashboard flips green to red
3. Investigates. The driver describes what they notice. SimDoctor retrieves the most relevant diagnostic knowledge from Atlas and asks Gemini to reason over the evidence.
4. Produces a report. Possible causes, urgency,safety warning,recommended checks and a confidence statement. Causes are always presented as hypotheses to verify never a confirmed diagnosis.
5. Answers questions. A chat assistant is grounded in the vehicle's live readings and the knowledge base, and cities which records it used.

# ⚠️DISCLAIMER⚠️
No real car is connected. SimDoctor simulates the drive, and all faults limits are simulation thresholds, not manufacture specification =( 

