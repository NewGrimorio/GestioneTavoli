import { configureStore } from "@reduxjs/toolkit";
import sessionsReducer from "../features/sessions/sessionsSlice.js";
import navigationReducer from "../features/navigation/navigationSlice.js";
import playersReducer from "../features/players/playersSlice.js";

export const store = configureStore({
  reducer: {
    navigation: navigationReducer,
    players: playersReducer,
    sessions: sessionsReducer,
  },
});
