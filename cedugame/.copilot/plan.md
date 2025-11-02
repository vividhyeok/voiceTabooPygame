# 🎮 VoiceTaboo → 웹 두들 게임 + 모바일 컨트롤러 (Supabase 연동)

## 0) 목표

* **폰=컨트롤러 / PC=호스트** 구조의 **정적 웹 게임**.
* **순위 저장은 Supabase**(이미 구성된 `leaderboard` 테이블 사용).
* **컨트롤 신호는 기본 Supabase Realtime**, **망 불안 시 로컬 WebSocket 폴백**(옵션).
* 컨트롤러 카메라 화면은 **표시하지 않음**. **인식 실패 시 “현재 인식이 안되고 있습니다!”** 배지만 표시.

---

## 1) 아키텍처 개요

```
[ctrl.html (모바일)] --(Realtime broadcast / WS 폴백)--> [host.html (PC/태블릿)]
                                 └──(선택)→ Supabase DB: leaderboard (점수 저장/조회)
```

* **데이터 경로**

  * 컨트롤 신호: Supabase **broadcast 채널(room-####)** 기본, 실패 시 **LAN WS 폴백**
  * 점수: Supabase **leaderboard** INSERT/SELECT (이미 RLS 정책 설정: public INSERT/SELECT 허용)

---

## 2) 파일 구조(신규/변경)

```
/web/
  host.html          # 호스트 게임 화면(Canvas)
  ctrl.html          # 모바일 컨트롤러(자이로/제스처 송신)
  lib/supabase.min.js (또는 CDN 사용)
  assets/            # 아이콘 등 (옵션)

# 옵션: 폴백용 로컬 WS 브리지(행사 당일 네트워크 문제 대비)
tools/server.py
```

---

## 3) 공통 상수/키 (코파일럿이 주입/치환)

```js
// TODO: 실제 값을 넣어 배포 전 바꾼다.
const SUPABASE_URL = 'https://xxxxx.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIs...';
```

* Supabase는 **anon key**만 사용(공개 전제).
* DB 테이블: `public.leaderboard (id, created_at now(), game_name, game_mode, score, device_id, player_name default 'Player')`
* RLS: `SELECT true`, `INSERT true` 정책 활성.

---

## 4) 통신 어댑터(코파일럿이 생성해야 할 공통 JS 패턴)

```js
class Transport {
  async subscribe(onmsg) {}
  async send(payload) {}
  close() {}
}

class SupabaseTx extends Transport {
  constructor(sb, room) {
    super();
    this.sb = sb;
    this.room = room;
    this.ch = null;
  }
  async subscribe(onmsg) {
    this.ch = this.sb.channel(`room-${this.room}`, { config:{ broadcast:{ ack:true } }});
    this.ch.on('broadcast', { event:'ctrl' }, ({payload}) => onmsg(payload)).subscribe();
  }
  async send(payload) {
    await this.ch?.send({ type:'broadcast', event:'ctrl', payload });
  }
  close(){ if (this.ch) this.sb.removeChannel(this.ch); }
}

class WSTx extends Transport {
  constructor(url) { super(); this.ws = new WebSocket(url); }
  async subscribe(onmsg) { this.ws.onmessage = (e)=> onmsg(JSON.parse(e.data)); }
  async send(payload) { if (this.ws.readyState===1) this.ws.send(JSON.stringify(payload)); }
  close(){ try{ this.ws.close(); }catch{} }
}

// 부팅 로직: Supabase 우선, 필요 시 WS 폴백
async function createTransport({ sb, room, wsUrl=null, force='supabase' }) {
  if (force==='ws' && wsUrl) return new WSTx(wsUrl);
  // 기본: Supabase
  try { return new SupabaseTx(sb, room); } catch { /* noop */ }
  // 폴백: WS
  if (wsUrl) return new WSTx(wsUrl);
  throw new Error('No transport available');
}
```

**메시지 스키마(공통)**

```js
// { type:'tilt'|'gesture'|'status', ax?:number, jump?:boolean, recog?:boolean, ts:number }
```

---

## 5) host.html 요구사항(코파일럿 구현)

* UI: **코드 입력** + **시작 버튼**, **현재 코드 배지**, **인식상태 배지**(“현재 인식이 안되고 있습니다!”).
* Canvas 900×600, 60fps:

  * 물리: 중력 `vy += 0.6`, 마찰 `vx*=0.95; vy*=0.95`
  * 충돌: 바닥/벽, 점프 시 `vy = -12`(250ms 쿨다운)
* subscribe 후 수신 처리:

  * `{type:'tilt', ax}` → `vx += ax * 0.6`
  * `{type:'gesture', jump:true}` → 점프 적용
  * `{type:'status', recog:false}` 또는 일정 시간 미수신 → **인식 실패 배지 ON**
* 페이지 이탈 시 채널/소켓 정리.

---

## 6) ctrl.html 요구사항(코파일럿 구현)

* UI: **코드 입력**, **연결 버튼**, **점프 버튼**, **상태 텍스트**.
* 연결 시 채널 구독.
* **A안(기본)**: DeviceMotion/Orientation

  * iOS: `DeviceMotionEvent.requestPermission()` 처리
  * 20Hz(50ms)로 `ax`만 전송 `{type:'tilt', ax, recog:true, ts}`
* **B안(선택)**: MediaPipe Hands (비표시)

  * `<video>`는 `display:none`.
  * 손 미검출 500ms 이상 시 `{type:'status', recog:false}` 전송.
  * 특정 제스처 검출 시 `{type:'gesture', jump:true}` 전송.
* 점프 버튼은 항상 수동 전송 가능.
* 에러/미연결 시 상태 텍스트 갱신.

---

## 7) 리더보드 연동(기존 Supabase DB 사용) — 코파일럿이 붙일 함수

```js
// 공용: 초기화
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// 장치 식별자
const DEVICE_KEY='vt_device_id';
let deviceId = localStorage.getItem(DEVICE_KEY) || (crypto?.randomUUID?.() || String(Date.now()));
localStorage.setItem(DEVICE_KEY, deviceId);

// 업로드
async function submitScore({ game_name, game_mode='normal', score, player_name='Player' }){
  const { data, error } = await supabase
    .from('leaderboard')
    .insert([{ game_name, game_mode, score, device_id: deviceId, player_name }])
    .select();
  if (error) console.error('[submitScore]', error);
  return data?.[0] ?? null;
}

// 조회
async function fetchLeaderboard({ game_name, game_mode='normal', limit=10 }){
  const { data, error } = await supabase
    .from('leaderboard').select('*')
    .eq('game_name', game_name).eq('game_mode', game_mode)
    .order('score', { ascending:false }).limit(limit);
  if (error) { console.error('[fetchLeaderboard]', error); return []; }
  return data;
}

// (선택) 실시간 반영
const boardCh = supabase.channel('leaderboard-ch')
  .on('postgres_changes', { event:'INSERT', schema:'public', table:'leaderboard' }, () => renderBoard?.())
  .subscribe();
```

---

## 8) 로컬 WS 폴백 서버 (옵션, 행사 당일 플랜 B)

`tools/server.py`

```python
import asyncio, websockets, json
clients=set()
async def handler(ws):
    clients.add(ws)
    try:
        async for msg in ws:
            data=json.loads(msg)
            for c in list(clients):
                if c!=ws: await c.send(json.dumps(data))
    finally:
        clients.remove(ws)
asyncio.run(websockets.serve(handler,"0.0.0.0",8765))
```

실행:

```bash
pip install websockets
python tools/server.py
python -m http.server 8000  # /web를 루트로 서빙
```

* 폰에서 `http://<노트북IP>:8000/web/ctrl.html` 접속
* 어댑터는 `ws://<노트북IP>:8765`로 연결 시도(토글 또는 쿼리로 지정 가능)

---

## 9) 배포 & 테스트

* **로컬 테스트**: `python -m http.server 8000` → `http://localhost:8000/web/host.html`
* **Vercel/Pages**: 정적 업로드(빌드 없음)
* **모바일 권한**: iOS는 사용자 제스처 후 모션 권한 요청 필요
* **리허설 체크**: 행사장 Wi-Fi에서 **AP Isolation** 유무 확인(노트북 IP로 폰 접속 가능한지)

---

## 10) 수용 기준(Acceptance)

* 두 기기(PC=host, 모바일=ctrl)에서 1분 내 연결/플레이.
* 틸트로 좌우 이동, 점프 제스처/버튼 동작.
* 0.5~1초 이상 인식 실패 시 호스트에 **“현재 인식이 안되고 있습니다!”** 배지 표시.
* 게임 종료 시 `submitScore()`로 Supabase 테이블에 레코드 생성.
* (선택) Realtime 켜면 다른 화면의 순위표도 자동 갱신.

---

## 11) 코파일럿 작업 지시(한 줄 프롬프트)

> “/web/host.html 과 /web/ctrl.html을 생성하고, 위 ‘통신 어댑터/요구사항’에 맞춰 Supabase Realtime 기본 + WS 폴백을 구현하라. host는 두들 게임(중력/점프/벽충돌)을 캔버스로 렌더, ctrl는 devicemotion 20Hz 전송 및 점프 버튼, 인식 실패(status) 이벤트를 보낸다. 리더보드는 위 함수로 INSERT/SELECT 연결. 카메라 영상은 표시하지 말고, 손 미검출 시 recog=false 이벤트만 보낸다. 상단 상수에는 SUPABASE_URL/ANON_KEY를 치환하도록 TODO를 넣어라.”

---

### 메모

* **카메라 비표시**: `<video style="display:none">` 또는 캔버스 미렌더.
* **지연 대비**: 전송 주기 50ms(20Hz), 필요 시 10~15Hz로 낮추기.
* **보안**: service_role 절대 사용 금지. anon만.