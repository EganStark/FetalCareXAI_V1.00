# FetalCare XAI deployment

## Recommended host

Use **Render with Docker** for the first production release. The application is a
single Flask service and includes native LightGBM libraries, scikit-learn model
artifacts, LIME, and Matplotlib. A container host is a more predictable fit than
splitting this version across Vercel serverless functions.

Vercel remains a good future option if the frontend is separated from the API.
That split is not necessary for the current release and adds CORS, two deployments,
and two monitoring surfaces.

## Local production check

```bash
docker build -t fetalcare-xai .
docker run --rm -p 5000:5000 fetalcare-xai
```

Open `http://127.0.0.1:5000` and verify `http://127.0.0.1:5000/health`.

## Render (later)

1. Connect this GitHub repository in Render.
2. Create the service from `render.yaml`.
3. Use a paid Starter instance or larger to avoid cold-start delays during model loading.
4. Confirm the health check, prediction, and explanation flows before sharing the URL.
5. Keep auto-deploy disabled until model tests pass in CI.

## Privacy and safety

- Do not add raw CTG inputs to analytics, logs, crash reports, or URLs.
- Keep the research-use disclaimer visible.
- Use HTTPS in production.
- Treat generated results as transient; this release has no accounts or history.
- Complete clinical validation and the applicable regulatory review before any clinical use.
