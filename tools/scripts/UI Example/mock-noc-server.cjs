const { WebSocketServer } = require("ws");

const port = Number(process.env.FITNESS_WS_PORT || process.env.NOC_WS_PORT || 8091);
const path = process.env.FITNESS_WS_PATH || process.env.NOC_WS_PATH || "/fitness";

const workoutNames = ["Morning Run", "Strength Circuit", "Mobility Session", "Core Finisher"];
const weekDays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const logEvents = [
  "Warm-up complete. Cardiovascular load entering target zone.",
  "Hydration reminder acknowledged.",
  "Cadence stabilized after interval block.",
  "Recovery trend improved after cooldown period.",
  "Step pace accelerated during power walk segment.",
  "Breathing pattern normalized post sprint."
];

const workouts = [
  { name: workoutNames[0], durationMinutes: 38, calories: 426, intensity: "good" },
  { name: workoutNames[1], durationMinutes: 42, calories: 352, intensity: "watch" },
  { name: workoutNames[2], durationMinutes: 20, calories: 118, intensity: "good" },
  { name: workoutNames[3], durationMinutes: 16, calories: 101, intensity: "good" }
];

const weekly = [
  { day: weekDays[0], completion: 71 },
  { day: weekDays[1], completion: 82 },
  { day: weekDays[2], completion: 77 },
  { day: weekDays[3], completion: 89 },
  { day: weekDays[4], completion: 84 },
  { day: weekDays[5], completion: 92 },
  { day: weekDays[6], completion: 79 }
];

const metrics = {
  heartRate: 121,
  calories: 1148,
  steps: 7810,
  distanceKm: 5.71,
  hydrationLiters: 1.87,
  sleepHours: 7.3,
  activeMinutes: 48,
  recovery: 76,
  stress: 38
};

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function pickDelta(range) {
  return Math.random() * range * 2 - range;
}

function toLog(message) {
  return `${new Date().toLocaleTimeString("en-GB")} ${message}`;
}

const wss = new WebSocketServer({ port, path });

console.log(`[mock-fitness] ws://localhost:${port}${path}`);

wss.on("connection", (socket) => {
  console.log("[mock-fitness] client connected");

  socket.send(
    JSON.stringify({
      metrics,
      weekly,
      workouts,
      logs: [
        toLog("Live fitness stream established."),
        toLog("Syncing wearable and workout session data.")
      ]
    })
  );

  const timer = setInterval(() => {
    metrics.heartRate = clamp(metrics.heartRate + pickDelta(5.5), 96, 166);
    metrics.calories = clamp(metrics.calories + Math.max(pickDelta(12), 2), 550, 2800);
    metrics.steps = clamp(metrics.steps + Math.max(pickDelta(90), 8), 2800, 22000);
    metrics.distanceKm = clamp(metrics.distanceKm + Math.max(pickDelta(0.08), 0.01), 1.3, 17.5);
    metrics.hydrationLiters = clamp(metrics.hydrationLiters + Math.max(pickDelta(0.05), 0.003), 0.5, 5);
    metrics.sleepHours = clamp(metrics.sleepHours + pickDelta(0.07), 5.8, 8.8);
    metrics.activeMinutes = clamp(metrics.activeMinutes + Math.max(pickDelta(2.6), 0.3), 16, 160);
    metrics.recovery = clamp(metrics.recovery + pickDelta(2.2), 48, 98);
    metrics.stress = clamp(metrics.stress + pickDelta(2.5), 18, 82);

    const weeklyPayload = weekly.map((day) => ({
      ...day,
      completion: clamp(day.completion + pickDelta(2.6), 62, 100)
    }));

    const workoutPayload = workouts.map((workout) => {
      const nextIntensity =
        workout.intensity === "watch" && Math.random() < 0.45
          ? "good"
          : workout.intensity === "good" && Math.random() < 0.15
            ? "watch"
            : workout.intensity;

      return {
        ...workout,
        calories: Math.round(clamp(workout.calories + pickDelta(18), 80, 620)),
        intensity: nextIntensity
      };
    });

    const payload = {
      metrics,
      weekly: weeklyPayload,
      workouts: workoutPayload,
      log: logEvents[Math.floor(Math.random() * logEvents.length)]
    };

    if (socket.readyState === socket.OPEN) {
      socket.send(JSON.stringify(payload));
    }
  }, 2400);

  socket.on("close", () => {
    clearInterval(timer);
    console.log("[mock-fitness] client disconnected");
  });

  socket.on("error", () => {
    clearInterval(timer);
  });
});
