import { useEffect, useState } from "react";

export type GoalTone = "green" | "amber" | "blue";

export type FitnessMetrics = {
  heartRate: number;
  calories: number;
  steps: number;
  distanceKm: number;
  hydrationLiters: number;
  sleepHours: number;
  activeMinutes: number;
  recovery: number;
  stress: number;
};

export type Goal = {
  label: string;
  current: number;
  target: number;
  unit: string;
  tone: GoalTone;
  progress: number;
};

export type WeeklyProgress = {
  day: string;
  completion: number;
};

export type WorkoutIntensity = "good" | "watch";

export type WorkoutSession = {
  name: string;
  durationMinutes: number;
  calories: number;
  intensity: WorkoutIntensity;
};

export type SocketState = "disabled" | "connecting" | "open" | "closed" | "error";
export type FeedMode = "simulated" | "live";
export type FeedPreference = "auto" | "live" | "simulated";

type FitnessPacket = {
  metrics?: Partial<FitnessMetrics>;
  weekly?: WeeklyProgress[];
  workouts?: WorkoutSession[];
  log?: string;
  logs?: string[];
};

const logEvents = [
  "Warm-up complete. Cardiovascular load entering target zone.",
  "Hydration reminder acknowledged.",
  "Cadence stabilized after interval block.",
  "Recovery trend improved after cooldown period.",
  "Step pace accelerated during power walk segment.",
  "Breathing pattern normalized post sprint."
];

const baseWeekly: WeeklyProgress[] = [
  { day: "Mon", completion: 71 },
  { day: "Tue", completion: 82 },
  { day: "Wed", completion: 77 },
  { day: "Thu", completion: 89 },
  { day: "Fri", completion: 84 },
  { day: "Sat", completion: 92 },
  { day: "Sun", completion: 79 }
];

const baseWorkouts: WorkoutSession[] = [
  { name: "Morning Run", durationMinutes: 38, calories: 426, intensity: "good" },
  { name: "Strength Circuit", durationMinutes: 42, calories: 352, intensity: "watch" },
  { name: "Mobility Session", durationMinutes: 20, calories: 118, intensity: "good" },
  { name: "Core Finisher", durationMinutes: 16, calories: 101, intensity: "good" }
];

const baseMetrics: FitnessMetrics = {
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

function buildGoals(metrics: FitnessMetrics): Goal[] {
  const goals = [
    { label: "Steps", current: Math.round(metrics.steps), target: 12000, unit: "", tone: "green" as GoalTone },
    { label: "Hydration", current: Number(metrics.hydrationLiters.toFixed(2)), target: 3.2, unit: "L", tone: "blue" as GoalTone },
    { label: "Active Minutes", current: Math.round(metrics.activeMinutes), target: 90, unit: "min", tone: "amber" as GoalTone },
    { label: "Calories", current: Math.round(metrics.calories), target: 1800, unit: "kcal", tone: "green" as GoalTone }
  ];

  return goals.map((goal) => ({
    ...goal,
    progress: clamp((goal.current / goal.target) * 100, 0, 100)
  }));
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function pickDelta(range: number): number {
  return Math.random() * range * 2 - range;
}

function stampLog(line: string): string {
  return `${new Date().toLocaleTimeString("en-GB")} ${line}`;
}

function seedLogs(): string[] {
  return Array.from({ length: 4 }, () => {
    const event = logEvents[Math.floor(Math.random() * logEvents.length)];
    return stampLog(event);
  });
}

function normalizePacket(raw: unknown): FitnessPacket | null {
  if (!raw || typeof raw !== "object") {
    return null;
  }

  const root = raw as Record<string, unknown>;
  const payload =
    root.payload && typeof root.payload === "object"
      ? (root.payload as Record<string, unknown>)
      : root;

  const packet: FitnessPacket = {};

  if (payload.metrics && typeof payload.metrics === "object") {
    packet.metrics = payload.metrics as Partial<FitnessMetrics>;
  }
  if (Array.isArray(payload.weekly)) {
    packet.weekly = payload.weekly as WeeklyProgress[];
  }
  if (Array.isArray(payload.workouts)) {
    packet.workouts = payload.workouts as WorkoutSession[];
  }
  if (typeof payload.log === "string") {
    packet.log = payload.log;
  }
  if (Array.isArray(payload.logs)) {
    packet.logs = payload.logs as string[];
  }

  return packet;
}

export function useFitnessFeed(preference: FeedPreference = "auto") {
  const [metrics, setMetrics] = useState<FitnessMetrics>(baseMetrics);
  const [weekly, setWeekly] = useState<WeeklyProgress[]>(baseWeekly);
  const [workouts, setWorkouts] = useState<WorkoutSession[]>(baseWorkouts);
  const [logs, setLogs] = useState<string[]>(seedLogs());
  const [goals, setGoals] = useState<Goal[]>(buildGoals(baseMetrics));

  const wsUrl = (import.meta.env.VITE_FITNESS_WS_URL || import.meta.env.VITE_NOC_WS_URL) as
    | string
    | undefined;
  const wantsSocket = preference !== "simulated";
  const [mode, setMode] = useState<FeedMode>("simulated");
  const [socketState, setSocketState] = useState<SocketState>(
    wsUrl && wantsSocket ? "connecting" : "disabled"
  );

  useEffect(() => {
    if (!wsUrl || !wantsSocket) {
      setSocketState("disabled");
      setMode("simulated");
      return;
    }

    let ws: WebSocket | null = null;
    let reconnectHandle: number | undefined;
    let disposed = false;

    const connect = () => {
      if (disposed) return;
      setSocketState("connecting");

      try {
        ws = new WebSocket(wsUrl);
      } catch {
        setSocketState("error");
        if (preference === "auto") {
          setMode("simulated");
        }
        reconnectHandle = window.setTimeout(connect, 5000);
        return;
      }

      ws.onopen = () => {
        setSocketState("open");
        setMode("live");
      };

      ws.onmessage = (event: MessageEvent<string>) => {
        try {
          const parsed = JSON.parse(event.data) as unknown;
          const packet = normalizePacket(parsed);
          if (!packet) return;

          if (packet.metrics) {
            setMetrics((prev) => {
              return { ...prev, ...packet.metrics };
            });
          }
          if (packet.weekly) {
            setWeekly(packet.weekly);
          }
          if (packet.workouts) {
            setWorkouts(packet.workouts);
          }
          if (packet.logs && packet.logs.length > 0) {
            setLogs(packet.logs.slice(0, 6));
          }
          if (packet.log) {
            setLogs((prev) => [stampLog(packet.log as string), ...prev].slice(0, 6));
          }
        } catch {
          setLogs((prev) => [stampLog("Received malformed fitness payload."), ...prev].slice(0, 6));
        }
      };

      ws.onerror = () => {
        setSocketState("error");
        if (preference === "auto") {
          setMode("simulated");
        }
      };

      ws.onclose = () => {
        if (disposed) return;
        setSocketState("closed");
        if (preference === "auto") {
          setMode("simulated");
        }
        reconnectHandle = window.setTimeout(connect, 5000);
      };
    };

    connect();

    return () => {
      disposed = true;
      if (reconnectHandle) {
        window.clearTimeout(reconnectHandle);
      }
      if (ws && ws.readyState < WebSocket.CLOSING) {
        ws.close();
      }
    };
  }, [preference, wantsSocket, wsUrl]);

  useEffect(() => {
    setGoals(buildGoals(metrics));
  }, [metrics]);

  useEffect(() => {
    const runSimulation = preference === "simulated" || (preference === "auto" && mode === "simulated");
    if (!runSimulation) {
      return;
    }

    const metricsTimer = window.setInterval(() => {
      setMetrics((prev) => ({
        heartRate: clamp(prev.heartRate + pickDelta(5.5), 96, 166),
        calories: clamp(prev.calories + Math.max(pickDelta(12), 2), 550, 2800),
        steps: clamp(prev.steps + Math.max(pickDelta(88), 10), 2800, 22000),
        distanceKm: clamp(prev.distanceKm + Math.max(pickDelta(0.08), 0.01), 1.3, 17.5),
        hydrationLiters: clamp(prev.hydrationLiters + Math.max(pickDelta(0.05), 0.003), 0.5, 5),
        sleepHours: clamp(prev.sleepHours + pickDelta(0.07), 5.8, 8.8),
        activeMinutes: clamp(prev.activeMinutes + Math.max(pickDelta(2.7), 0.3), 16, 160),
        recovery: clamp(prev.recovery + pickDelta(2.2), 48, 98),
        stress: clamp(prev.stress + pickDelta(2.5), 18, 82)
      }));

      setWeekly((prev) =>
        prev.map((day) => ({
          ...day,
          completion: clamp(day.completion + pickDelta(2.6), 62, 100)
        }))
      );

      setWorkouts((prev) =>
        prev.map((workout) => ({
          ...workout,
          calories: Math.round(clamp(workout.calories + pickDelta(18), 80, 620)),
          intensity:
            workout.intensity === "watch" && Math.random() < 0.45
              ? "good"
              : workout.intensity === "good" && Math.random() < 0.15
                ? "watch"
                : workout.intensity
        }))
      );
    }, 2600);

    const logTimer = window.setInterval(() => {
      const event = logEvents[Math.floor(Math.random() * logEvents.length)];
      setLogs((prev) => [stampLog(event), ...prev].slice(0, 6));
    }, 5000);

    return () => {
      window.clearInterval(metricsTimer);
      window.clearInterval(logTimer);
    };
  }, [mode, preference]);

  return {
    metrics,
    goals,
    weekly,
    workouts,
    logs,
    mode,
    socketState
  };
}
