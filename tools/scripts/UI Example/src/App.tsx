import { useEffect, useMemo, useState } from "react";
import { FeedPreference, WeeklyProgress, useFitnessFeed } from "./nocData";

export default function App() {
  const [clock, setClock] = useState<string>(new Date().toLocaleTimeString("en-GB"));
  const [feedPreference, setFeedPreference] = useState<FeedPreference>("auto");
  const { metrics, goals, weekly, workouts, logs, mode, socketState } = useFitnessFeed(feedPreference);

  const elevatedLoad = metrics.heartRate > 148 || metrics.stress > 64;

  const kpis = useMemo(
    () => [
      { label: "Heart Rate", value: `${Math.round(metrics.heartRate)} bpm`, foot: "Target zone 122-151" },
      {
        label: "Active Calories",
        value: `${Math.round(metrics.calories).toLocaleString()} kcal`,
        foot: "Daily burn"
      },
      { label: "Steps", value: Math.round(metrics.steps).toLocaleString(), foot: "Goal 12,000" },
      { label: "Distance", value: `${metrics.distanceKm.toFixed(2)} km`, foot: "Movement volume" },
      { label: "Hydration", value: `${metrics.hydrationLiters.toFixed(2)} L`, foot: "Goal 3.20 L" },
      { label: "Sleep", value: `${metrics.sleepHours.toFixed(1)} h`, foot: "Goal 8.0 h" }
    ],
    [metrics]
  );

  useEffect(() => {
    const timer = window.setInterval(() => {
      setClock(new Date().toLocaleTimeString("en-GB"));
    }, 1000);
    return () => window.clearInterval(timer);
  }, []);

  const weeklyMax = Math.max(...weekly.map((item) => item.completion));

  const progressStyle = (item: WeeklyProgress) => ({
    height: `${(item.completion / Math.max(weeklyMax, 1)) * 100}%`
  });

  const sourceLabel = mode === "live" ? "Feed: Live" : "Feed: Simulated";
  const sourceClass = mode === "live" ? "healthy" : "warning";
  const desiredLabel = `Mode: ${feedPreference.toUpperCase()}`;

  return (
    <>
      <div className="bg-grid" aria-hidden="true" />
      <div className="bg-radial bg-radial-one" aria-hidden="true" />
      <div className="bg-radial bg-radial-two" aria-hidden="true" />

      <div className="app-shell">
        <header className="topbar panel reveal">
          <div>
            <p className="eyebrow">Performance Lab</p>
            <h1>JUSTYOUTRAINING</h1>
          </div>
          <div className="status-strip">
            <div className="status-pill healthy">Recovery: Trending Up</div>
            <div className={`status-pill ${elevatedLoad ? "warning" : "healthy"}`}>
              {elevatedLoad ? "Training Load: Elevated" : "Training Load: Balanced"}
            </div>
            <div className={`status-pill ${sourceClass}`}>{sourceLabel}</div>
            <div className="status-pill">{desiredLabel}</div>
            <div className="status-pill info">Socket: {socketState}</div>
            <div className="status-pill">Focus: Endurance + Strength</div>
            <div className="status-pill">Timestamp: {clock}</div>
          </div>
          <div className="feed-toggle" role="group" aria-label="Telemetry mode selection">
            <button
              type="button"
              className={`toggle-btn ${feedPreference === "auto" ? "active" : ""}`}
              onClick={() => setFeedPreference("auto")}
            >
              Auto
            </button>
            <button
              type="button"
              className={`toggle-btn ${feedPreference === "live" ? "active" : ""}`}
              onClick={() => setFeedPreference("live")}
            >
              Force Live
            </button>
            <button
              type="button"
              className={`toggle-btn ${feedPreference === "simulated" ? "active" : ""}`}
              onClick={() => setFeedPreference("simulated")}
            >
              Force Sim
            </button>
          </div>
        </header>

        <main className="dashboard-grid">
          <section className="panel span-8 reveal delay-1">
            <div className="panel-heading">
              <h2>Live Body Metrics</h2>
              <p>Updated every few seconds from current activity stream</p>
            </div>
            <div className="kpi-grid">
              {kpis.map((kpi) => (
                <article className="kpi-card" key={kpi.label}>
                  <h3>{kpi.label}</h3>
                  <p className="kpi-value">{kpi.value}</p>
                  <span className="kpi-foot">{kpi.foot}</span>
                </article>
              ))}
            </div>
          </section>

          <section className="panel span-4 reveal delay-2">
            <div className="panel-heading">
              <h2>Body State</h2>
              <p>Real-time readiness markers</p>
            </div>
            <div className="readiness-wrap">
              <article className="readiness-card">
                <p>Recovery Index</p>
                <strong>{Math.round(metrics.recovery)}%</strong>
                <div className="stack">
                  <div className="bar green" style={{ width: `${metrics.recovery}%` }} />
                </div>
              </article>

              <article className="readiness-card">
                <p>Stress Index</p>
                <strong>{Math.round(metrics.stress)}%</strong>
                <div className="stack">
                  <div className="bar amber" style={{ width: `${metrics.stress}%` }} />
                </div>
              </article>

              <article className="readiness-card">
                <p>Active Minutes</p>
                <strong>{Math.round(metrics.activeMinutes)} min</strong>
                <div className="stack">
                  <div className="bar blue" style={{ width: `${Math.min((metrics.activeMinutes / 90) * 100, 100)}%` }} />
                </div>
              </article>
            </div>
          </section>

          <section className="panel span-7 reveal delay-3">
            <div className="panel-heading">
              <h2>Weekly Progress</h2>
              <p>Goal completion trend over the past 7 days</p>
            </div>
            <div className="weekly-chart" role="img" aria-label="weekly goal completion chart">
              {weekly.map((item) => (
                <div className="weekly-col" key={item.day}>
                  <div className="weekly-bar-wrap">
                    <div className="weekly-bar" style={progressStyle(item)} />
                  </div>
                  <p className="weekly-value">{Math.round(item.completion)}%</p>
                  <p className="weekly-day">{item.day}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="panel span-5 reveal delay-4">
            <div className="panel-heading">
              <h2>Goal Progress</h2>
              <p>Daily targets and completion</p>
            </div>
            <div className="stack-wrap">
              {goals.map((goal) => (
                <div key={goal.label} className="goal-block">
                  <div className="stack-label">
                    <span>{goal.label}</span>
                    <span>
                      {goal.current.toLocaleString()} / {goal.target.toLocaleString()} {goal.unit}
                    </span>
                  </div>
                  <div className="stack">
                    <div className={`bar ${goal.tone}`} style={{ width: `${goal.progress}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="panel span-6 reveal delay-5">
            <div className="panel-heading">
              <h2>Workout Sessions</h2>
              <p>Recent blocks and current intensity</p>
            </div>
            <div className="site-grid">
              {workouts.map((session) => (
                <article className="site-card" key={session.name}>
                  <h3>{session.name}</h3>
                  <div className="site-meta">
                    <span>{session.durationMinutes} min</span>
                    <span className={`health-pill health-${session.intensity}`}>{session.intensity.toUpperCase()}</span>
                  </div>
                  <div className="site-meta">
                    <span>Calories</span>
                    <strong>{session.calories} kcal</strong>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="panel span-6 reveal delay-6">
            <div className="panel-heading">
              <h2>Live Timeline</h2>
              <p>Health and training events as they occur</p>
            </div>
            <ul className="log-list">
              {logs.map((line, idx) => {
                const split = line.indexOf(" ");
                const time = split > 0 ? line.slice(0, split) : line;
                const msg = split > 0 ? line.slice(split + 1) : "";
                return (
                  <li key={`${line}-${idx}`}>
                    <span className="log-time">{time}</span>
                    {msg}
                  </li>
                );
              })}
            </ul>
          </section>
        </main>
      </div>
    </>
  );
}
