# Runtime Environment Variables Setup

This project uses **runtime environment variable injection** for Next.js App Router with Docker + Nginx + Dokploy.

## How It Works

1. **Build Time**: Next.js builds a static export (no environment variables baked in)
2. **Runtime**: When the container starts, `generate-env.js` creates `/env.js` from Docker environment variables
3. **Client**: `app/layout.tsx` loads `/env.js` before React hydrates
4. **Access**: `lib/env.ts` provides safe access to environment variables

## Files

- `lib/env.ts` - Centralized environment variable access (server + client safe)
- `scripts/generate-env.js` - Generates `/env.js` at container startup
- `app/layout.tsx` - Loads `/env.js` before hydration
- `lib/api-client.ts` - Uses `getApiUrl()` from `lib/env.ts`
- `Dockerfile` - Generates `env.js` on container startup

## Dokploy Configuration

### Environment Variables (Runtime)

Set these in **Dokploy Environments** (NOT build arguments):

```
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### Important Notes

- ✅ Set `NEXT_PUBLIC_API_URL` in **Dokploy Environments** (runtime)
- ❌ Do NOT set it as a build argument
- ✅ The Docker image can be built once and reused
- ✅ Environment variables can be changed without rebuilding

## How to Verify

1. **Check `/env.js` is generated**:
   ```bash
   docker exec <container> cat /usr/share/nginx/html/env.js
   ```

2. **Check browser console**:
   - Open DevTools → Console
   - Type: `window.__ENV__`
   - Should show: `{ NEXT_PUBLIC_API_URL: "https://api.yourdomain.com" }`

3. **Check network tab**:
   - Look for `/env.js` request
   - Should return 200 with JavaScript content

## Troubleshooting

### Black Screen / API Not Working

1. **Check environment variable is set**:
   ```bash
   docker exec <container> env | grep NEXT_PUBLIC_API_URL
   ```

2. **Check env.js exists**:
   ```bash
   docker exec <container> ls -la /usr/share/nginx/html/env.js
   ```

3. **Check env.js content**:
   ```bash
   docker exec <container> cat /usr/share/nginx/html/env.js
   ```

4. **Check browser console**:
   - Look for errors about `NEXT_PUBLIC_API_URL`
   - Check if `window.__ENV__` is defined

### env.js Not Loading

1. **Check nginx is serving it**:
   - Visit: `https://yourdomain.com/env.js`
   - Should return JavaScript, not 404

2. **Check Cache-Control headers**:
   - `env.js` should have `no-cache` headers
   - See `nginx.conf` for configuration

## Architecture

```
┌─────────────────────────────────────────────────┐
│ Docker Container Startup                         │
│                                                  │
│ 1. Entrypoint script runs                       │
│ 2. generate-env.js reads NEXT_PUBLIC_API_URL   │
│ 3. Writes /usr/share/nginx/html/env.js          │
│ 4. Starts nginx                                  │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ Browser                                          │
│                                                  │
│ 1. Loads index.html                             │
│ 2. <Script src="/env.js"> loads (beforeInteractive)│
│ 3. window.__ENV__ = { NEXT_PUBLIC_API_URL: ... }│
│ 4. React hydrates                                │
│ 5. Components use getApiUrl() from lib/env.ts   │
└─────────────────────────────────────────────────┘
```

## Benefits

- ✅ **No rebuild required** - Change env vars without rebuilding image
- ✅ **App Router compatible** - Works with server components
- ✅ **Type safe** - TypeScript definitions for window.__ENV__
- ✅ **Production ready** - Used in Docker + Nginx + Dokploy
- ✅ **No process.env in client** - Follows Next.js best practices

