/**
 * Mini-jeu "Flappy Ballon" - ballon aux couleurs du Maroc, ambiance Coupe du
 * Monde 2026 (poteaux aux couleurs Mexique / Canada / États-Unis).
 * Implémentation 100% canvas, sans dépendance externe.
 */
import { useEffect, useRef, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import api from "@/lib/api";
import { Trophy } from "lucide-react";

const WIDTH = 360;
const HEIGHT = 540;
const GRAVITY = 0.45;
const FLAP_VELOCITY = -7.5;
const PIPE_WIDTH = 56;
const PIPE_GAP = 150;
const PIPE_SPEED = 2.6;
const PIPE_INTERVAL = 95; // frames entre deux poteaux
const BALL_RADIUS = 16;

// Thèmes de poteaux qui défilent (couleurs des pays hôtes 2026)
const THEMES = [
  { name: "Mexique", colors: ["#006847", "#ffffff", "#ce1126"] },
  { name: "Canada", colors: ["#ff0000", "#ffffff", "#ff0000"] },
  { name: "États-Unis", colors: ["#3c3b6e", "#ffffff", "#b22234"] },
];

function drawMoroccoBall(ctx, x, y, rotation) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(rotation);

  // Ballon rouge (drapeau marocain)
  ctx.beginPath();
  ctx.arc(0, 0, BALL_RADIUS, 0, Math.PI * 2);
  ctx.fillStyle = "#c1272d";
  ctx.fill();
  ctx.lineWidth = 2;
  ctx.strokeStyle = "#006233";
  ctx.stroke();

  // Étoile verte à 5 branches (pentagramme du drapeau marocain)
  ctx.fillStyle = "#006233";
  const spikes = 5;
  const outerR = BALL_RADIUS * 0.55;
  const innerR = outerR * 0.5;
  ctx.beginPath();
  for (let i = 0; i < spikes * 2; i++) {
    const r = i % 2 === 0 ? outerR : innerR;
    const a = (Math.PI / spikes) * i - Math.PI / 2;
    const px = Math.cos(a) * r;
    const py = Math.sin(a) * r;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.closePath();
  ctx.fill();

  ctx.restore();
}

function drawPipe(ctx, x, gapY, themeColors) {
  const [c1, c2, c3] = themeColors;

  // Poteau du haut
  drawPost(ctx, x, 0, gapY, c1, c2, c3);
  // Poteau du bas
  drawPost(ctx, x, gapY + PIPE_GAP, HEIGHT - (gapY + PIPE_GAP), c1, c2, c3);
}

function drawPost(ctx, x, y, h, c1, c2, c3) {
  if (h <= 0) return;
  const stripeH = Math.max(1, h / 6);
  for (let i = 0; i < 6; i++) {
    ctx.fillStyle = [c1, c2, c3, c1, c2, c3][i % 6];
    ctx.fillRect(x, y + i * stripeH, PIPE_WIDTH, stripeH + 1);
  }
  // Bordure "but"
  ctx.strokeStyle = "rgba(0,0,0,0.25)";
  ctx.lineWidth = 2;
  ctx.strokeRect(x, y, PIPE_WIDTH, h);
}

export default function GamePage() {
  const { user, loading: authLoading } = useAuth();
  if (authLoading) return null;
  if (!user || !user.id) return <Navigate to="/login" replace />;

  const canvasRef = useRef(null);
  const [score, setScore] = useState(0);
  const [best, setBest] = useState(() => {
    try {
      return Number(sessionStorage.getItem("flappy_best_score") || 0);
    } catch {
      return 0;
    }
  });
  const [status, setStatus] = useState("ready"); // ready | playing | over
  const [leaderboard, setLeaderboard] = useState([]);

  const loadLeaderboard = () => {
    api.get("/game/leaderboard").then(({ data }) => setLeaderboard(data)).catch(() => {});
  };

  useEffect(() => {
    loadLeaderboard();
  }, []);

  // Sur mobile, on remonte en haut de page pour exploiter tout l'écran
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  // État du jeu conservé dans une ref pour éviter les re-renders à chaque frame
  const state = useRef({
    y: HEIGHT / 2,
    vy: 0,
    rotation: 0,
    pipes: [],
    frame: 0,
    score: 0,
    themeIndex: 0,
  });

  const reset = () => {
    state.current = {
      y: HEIGHT / 2,
      vy: 0,
      rotation: 0,
      pipes: [],
      frame: 0,
      score: 0,
      themeIndex: 0,
    };
    setScore(0);
  };

  const flap = () => {
    if (status === "ready") {
      reset();
      setStatus("playing");
      state.current.vy = FLAP_VELOCITY;
      return;
    }
    if (status === "over") {
      reset();
      setStatus("playing");
      state.current.vy = FLAP_VELOCITY;
      return;
    }
    state.current.vy = FLAP_VELOCITY;
  };

  useEffect(() => {
    const handleKey = (e) => {
      if (e.code === "Space" || e.code === "ArrowUp") {
        e.preventDefault();
        flap();
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    let raf;

    const loop = () => {
      const s = state.current;
      ctx.clearRect(0, 0, WIDTH, HEIGHT);

      // Fond : ciel + pelouse
      const sky = ctx.createLinearGradient(0, 0, 0, HEIGHT);
      sky.addColorStop(0, "#8ecdf0");
      sky.addColorStop(1, "#cdeefc");
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, WIDTH, HEIGHT - 40);

      ctx.fillStyle = "#3a9b4c";
      ctx.fillRect(0, HEIGHT - 40, WIDTH, 40);
      ctx.strokeStyle = "rgba(255,255,255,0.6)";
      ctx.lineWidth = 2;
      for (let i = 0; i < WIDTH; i += 24) {
        ctx.beginPath();
        ctx.moveTo(i, HEIGHT - 40);
        ctx.lineTo(i + 12, HEIGHT);
        ctx.stroke();
      }

      if (status === "playing") {
        s.frame++;

        // Physique du ballon
        s.vy += GRAVITY;
        s.y += s.vy;
        s.rotation = Math.max(-0.5, Math.min(1.2, s.vy / 10));

        // Génération des poteaux
        if (s.frame % PIPE_INTERVAL === 0) {
          const gapY = 60 + Math.random() * (HEIGHT - 40 - PIPE_GAP - 120);
          s.pipes.push({ x: WIDTH, gapY, theme: THEMES[s.themeIndex % THEMES.length], passed: false });
          s.themeIndex++;
        }

        // Déplacement + score + collisions
        for (const pipe of s.pipes) {
          pipe.x -= PIPE_SPEED;

          if (!pipe.passed && pipe.x + PIPE_WIDTH < WIDTH / 2 - BALL_RADIUS) {
            pipe.passed = true;
            s.score++;
            setScore(s.score);
          }

          const ballX = WIDTH / 2;
          const hitX = ballX + BALL_RADIUS > pipe.x && ballX - BALL_RADIUS < pipe.x + PIPE_WIDTH;
          const hitY = s.y - BALL_RADIUS < pipe.gapY || s.y + BALL_RADIUS > pipe.gapY + PIPE_GAP;
          if (hitX && hitY) {
            endGame(s.score);
          }
        }
        s.pipes = s.pipes.filter((p) => p.x + PIPE_WIDTH > 0);

        // Sol / plafond
        if (s.y + BALL_RADIUS > HEIGHT - 40 || s.y - BALL_RADIUS < 0) {
          endGame(s.score);
        }
      }

      // Poteaux
      for (const pipe of s.pipes) {
        drawPipe(ctx, pipe.x, pipe.gapY, pipe.theme.colors);
      }

      // Ballon
      drawMoroccoBall(ctx, WIDTH / 2, s.y, s.rotation);

      raf = requestAnimationFrame(loop);
    };

    const endGame = (finalScore) => {
      setStatus("over");
      setBest((b) => {
        const nb = Math.max(b, finalScore);
        try {
          sessionStorage.setItem("flappy_best_score", String(nb));
        } catch {
          /* ignore */
        }
        return nb;
      });
      api
        .post("/game/score", { score: finalScore })
        .then(() => loadLeaderboard())
        .catch(() => {});
    };

    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  return (
    <div className="max-w-md mx-auto px-3 sm:px-6 pb-16 mt-1 sm:mt-4">
      <div className="text-center mb-1 sm:mb-3">
        <h1 className="display text-lg sm:text-3xl font-black uppercase tracking-tight">
          Flappy <span className="text-primary">Ballon</span>
        </h1>
        <p className="hidden sm:block text-xs sm:text-sm text-muted-foreground mt-1">
          Le ballon du Maroc traverse les buts USA · Canada · Mexique 🇲🇦
        </p>
      </div>

      <div className="flex items-center justify-between mb-1 sm:mb-2 text-sm font-bold uppercase tracking-wide">
        <span>Score : {score}</span>
        <span className="text-muted-foreground">Record : {best}</span>
      </div>

      <div
        className="relative mx-auto rounded-lg overflow-hidden border border-border cursor-pointer select-none"
        style={{
          width: `min(100%, calc((100vh - 230px) * ${WIDTH} / ${HEIGHT}))`,
          aspectRatio: `${WIDTH} / ${HEIGHT}`,
        }}
        onClick={flap}
        onTouchStart={(e) => {
          e.preventDefault();
          flap();
        }}
        data-testid="flappy-game-canvas-wrapper"
      >
        <canvas
          ref={canvasRef}
          width={WIDTH}
          height={HEIGHT}
          className="block w-full h-full"
          data-testid="flappy-game-canvas"
        />

        {status !== "playing" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/50 text-white text-center px-6">
            {status === "ready" ? (
              <>
                <p className="font-black uppercase text-lg mb-2">Prêt ?</p>
                <p className="text-sm">Clique, tape l'écran ou appuie sur Espace pour faire voler le ballon.</p>
              </>
            ) : (
              <>
                <p className="font-black uppercase text-xl mb-1">Perdu !</p>
                <p className="text-sm mb-2">Score : {score} · Record : {best}</p>
                <p className="text-sm">Clique pour rejouer</p>
              </>
            )}
          </div>
        )}
      </div>

      <p className="hidden sm:block text-center text-[11px] text-muted-foreground mt-3">
        Espace / clic / tap pour sauter. Évite les poteaux !
      </p>

      {leaderboard.length > 0 && (
        <div className="hidden sm:block mt-6 rounded-lg border border-border overflow-hidden">
          <div className="flex items-center gap-2 px-3 py-2 bg-secondary">
            <Trophy className="h-4 w-4 text-primary" />
            <span className="text-sm font-black uppercase tracking-wide">Classement Flappy Ballon</span>
          </div>
          <ul className="divide-y divide-border">
            {leaderboard.map((row, i) => (
              <li
                key={row.pseudo}
                className={`flex items-center justify-between px-3 py-1.5 text-sm ${
                  user && row.pseudo === user.pseudo ? "bg-secondary/60 font-bold" : ""
                }`}
              >
                <span className="flex items-center gap-2">
                  <span className="text-muted-foreground w-5 text-right">{i + 1}.</span>
                  {row.pseudo}
                </span>
                <span>{row.best_score}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
