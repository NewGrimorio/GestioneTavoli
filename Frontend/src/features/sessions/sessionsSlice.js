import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { api } from "../../api/client.js";

/** Wrap an API call so that a failure carries the user-readable message as payload. */
const guarded = (fn) => async (arg, { rejectWithValue }) => {
  try {
    return await fn(arg);
  } catch (error) {
    return rejectWithValue(error.message);
  }
};

export const fetchSessions = createAsyncThunk("sessions/fetchAll", () => api.listSessions());
export const fetchCurrentSession = createAsyncThunk("sessions/fetchCurrent", () =>
  api.getCurrentSession(),
);
export const fetchSession = createAsyncThunk("sessions/fetchOne", (id) => api.getSession(id));

export const createSession = createAsyncThunk("sessions/create", guarded(api.createSession));
export const addParticipant = createAsyncThunk(
  "sessions/addParticipant",
  guarded(({ sessionId, playerId }) => api.addParticipant(sessionId, playerId)),
);
export const removeParticipant = createAsyncThunk(
  "sessions/removeParticipant",
  guarded(({ sessionId, playerId }) => api.removeParticipant(sessionId, playerId)),
);
export const generateTables = createAsyncThunk("sessions/generate", guarded(api.generateTables));
export const closeSession = createAsyncThunk("sessions/close", guarded(api.closeSession));
export const deleteSession = createAsyncThunk(
  "sessions/delete",
  guarded(async (id) => {
    await api.deleteSession(id);
    return id;
  }),
);

const initialState = {
  list: [],
  listStatus: "idle", // idle | loading | succeeded | failed
  current: null, // the open session (full read), or null
  currentStatus: "idle",
  detail: null, // the session being viewed, or null
  detailStatus: "idle",
  error: null,
};

/** Apply a fresh copy of a session wherever it is held, and invalidate the list. */
function absorb(state, session) {
  if (state.current?.id === session.id) state.current = session;
  if (state.detail?.id === session.id) state.detail = session;
  state.listStatus = "idle";
}

const sessionsSlice = createSlice({
  name: "sessions",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchSessions.pending, (state) => {
        state.listStatus = "loading";
        state.error = null;
      })
      .addCase(fetchSessions.fulfilled, (state, action) => {
        state.listStatus = "succeeded";
        state.list = action.payload;
      })
      .addCase(fetchSessions.rejected, (state, action) => {
        state.listStatus = "failed";
        state.error = action.error.message;
      })

      .addCase(fetchCurrentSession.pending, (state) => {
        state.currentStatus = "loading";
        state.error = null;
      })
      .addCase(fetchCurrentSession.fulfilled, (state, action) => {
        state.currentStatus = "succeeded";
        state.current = action.payload;
      })
      .addCase(fetchCurrentSession.rejected, (state, action) => {
        state.currentStatus = "failed";
        state.error = action.error.message;
      })

      .addCase(fetchSession.pending, (state) => {
        state.detailStatus = "loading";
        state.detail = null;
        state.error = null;
      })
      .addCase(fetchSession.fulfilled, (state, action) => {
        state.detailStatus = "succeeded";
        state.detail = action.payload;
      })
      .addCase(fetchSession.rejected, (state, action) => {
        state.detailStatus = "failed";
        state.error = action.error.message;
      })

      .addCase(createSession.fulfilled, (state, action) => {
        // The new session is open; whatever was open before is now closed.
        state.current = action.payload;
        state.currentStatus = "succeeded";
        state.detail = action.payload;
        state.detailStatus = "succeeded";
        state.listStatus = "idle";
      })
      .addCase(addParticipant.fulfilled, (state, action) => absorb(state, action.payload))
      .addCase(removeParticipant.fulfilled, (state, action) => absorb(state, action.payload))
      .addCase(generateTables.fulfilled, (state, action) => absorb(state, action.payload))
      .addCase(closeSession.fulfilled, (state, action) => {
        absorb(state, action.payload);
        if (state.current?.id === action.payload.id) state.current = null;
      })
      .addCase(deleteSession.fulfilled, (state, action) => {
        state.list = state.list.filter((s) => s.id !== action.payload);
        if (state.current?.id === action.payload) state.current = null;
        if (state.detail?.id === action.payload) state.detail = null;
      });
  },
});

export default sessionsSlice.reducer;

export const selectSessions = (state) => state.sessions.list;
export const selectSessionsStatus = (state) => state.sessions.listStatus;
export const selectCurrentSession = (state) => state.sessions.current;
export const selectCurrentSessionStatus = (state) => state.sessions.currentStatus;
export const selectSessionDetail = (state) => state.sessions.detail;
export const selectSessionDetailStatus = (state) => state.sessions.detailStatus;
export const selectSessionsError = (state) => state.sessions.error;
