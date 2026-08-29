import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { api } from "../../api/client.js";

export const fetchSessions = createAsyncThunk("sessions/fetchAll", () => api.listSessions());

export const fetchSession = createAsyncThunk("sessions/fetchOne", (id) => api.getSession(id));

export const createSession = createAsyncThunk(
  "sessions/create",
  async (payload, { rejectWithValue }) => {
    try {
      return await api.createSession(payload);
    } catch (error) {
      return rejectWithValue(error.message);
    }
  },
);

export const deleteSession = createAsyncThunk(
  "sessions/delete",
  async (id, { rejectWithValue }) => {
    try {
      await api.deleteSession(id);
      return id;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  },
);

const sessionsSlice = createSlice({
  name: "sessions",
  initialState: {
    list: [],
    listStatus: "idle", // idle | loading | succeeded | failed
    current: null, // full session with rounds, or null
    currentStatus: "idle",
    error: null,
  },
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
      .addCase(fetchSession.pending, (state) => {
        state.currentStatus = "loading";
        state.current = null;
        state.error = null;
      })
      .addCase(fetchSession.fulfilled, (state, action) => {
        state.currentStatus = "succeeded";
        state.current = action.payload;
      })
      .addCase(fetchSession.rejected, (state, action) => {
        state.currentStatus = "failed";
        state.error = action.error.message;
      })
      .addCase(createSession.fulfilled, (state, action) => {
        state.current = action.payload;
        state.currentStatus = "succeeded";
        // Force a fresh list next time it is shown.
        state.listStatus = "idle";
      })
      .addCase(deleteSession.fulfilled, (state, action) => {
        state.list = state.list.filter((e) => e.id !== action.payload);
        if (state.current?.id === action.payload) state.current = null;
      });
  },
});

export default sessionsSlice.reducer;

export const selectSessions = (state) => state.sessions.list;
export const selectSessionsStatus = (state) => state.sessions.listStatus;
export const selectCurrentSession = (state) => state.sessions.current;
export const selectCurrentSessionStatus = (state) => state.sessions.currentStatus;
export const selectSessionsError = (state) => state.sessions.error;
