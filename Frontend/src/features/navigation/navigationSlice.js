import { createSlice } from "@reduxjs/toolkit";

/**
 * Which screen is shown. Three sections plus the detail view of one session;
 * no router library is needed at this size.
 *   { name: "sessions" } | { name: "new-session" } | { name: "players" }
 *   | { name: "session", id: number }
 */
const navigationSlice = createSlice({
  name: "navigation",
  initialState: { view: { name: "sessions" } },
  reducers: {
    navigate(state, action) {
      state.view = action.payload;
    },
  },
});

export const { navigate } = navigationSlice.actions;
export default navigationSlice.reducer;

export const selectView = (state) => state.navigation.view;
