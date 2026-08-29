import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { api } from "../../api/client.js";

export const fetchPlayers = createAsyncThunk("players/fetchAll", () => api.listPlayers());

export const addPlayer = createAsyncThunk("players/add", async (name, { rejectWithValue }) => {
  try {
    return await api.createPlayer(name);
  } catch (error) {
    return rejectWithValue(error.message);
  }
});

const byName = (a, b) => a.name.localeCompare(b.name, "it");

const playersSlice = createSlice({
  name: "players",
  initialState: {
    items: [],
    status: "idle", // idle | loading | succeeded | failed
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchPlayers.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(fetchPlayers.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.items = action.payload;
      })
      .addCase(fetchPlayers.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message;
      })
      .addCase(addPlayer.fulfilled, (state, action) => {
        state.items = [...state.items, action.payload].sort(byName);
      });
  },
});

export default playersSlice.reducer;

export const selectPlayers = (state) => state.players.items;
export const selectPlayersStatus = (state) => state.players.status;
export const selectPlayersError = (state) => state.players.error;
