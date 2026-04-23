const express = require("express");
const { createProxyMiddleware } = require("http-proxy-middleware");
const jwt = require("jsonwebtoken");
const morgan = require("morgan");

const app = express();
const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET_KEY;
const USER_SERVICE_URL = process.env.USER_SERVICE_URL || "http://user-service";
const TASK_SERVICE_URL = process.env.TASK_SERVICE_URL || "http://task-service";

app.use(morgan("combined"));

app.get("/health", (req, res) => {
  res.json({ status: "ok", service: "api-gateway" });
});

// Auth middleware — skipped for register/login
function requireAuth(req, res, next) {
  const auth = req.headers["authorization"];
  if (!auth || !auth.startsWith("Bearer ")) {
    return res.status(401).json({ error: "Missing or invalid Authorization header" });
  }
  try {
    jwt.verify(auth.slice(7), JWT_SECRET);
    next();
  } catch {
    res.status(401).json({ error: "Invalid token" });
  }
}

// User service — register/login are public; /me requires auth
app.use(
  "/api/users/register",
  createProxyMiddleware({
    target: USER_SERVICE_URL,
    changeOrigin: true,
    pathRewrite: { "^/api/users/register": "/register" },
  })
);

app.use(
  "/api/users/login",
  createProxyMiddleware({
    target: USER_SERVICE_URL,
    changeOrigin: true,
    pathRewrite: { "^/api/users/login": "/login" },
  })
);

app.use(
  "/api/users",
  requireAuth,
  createProxyMiddleware({
    target: USER_SERVICE_URL,
    changeOrigin: true,
    pathRewrite: { "^/api/users": "" },
  })
);

// Task service — all routes require auth
app.use(
  "/api/tasks",
  requireAuth,
  createProxyMiddleware({
    target: TASK_SERVICE_URL,
    changeOrigin: true,
    pathRewrite: { "^/api/tasks": "/tasks" },
  })
);

app.listen(PORT, () => {
  console.log(`API Gateway running on port ${PORT}`);
});
