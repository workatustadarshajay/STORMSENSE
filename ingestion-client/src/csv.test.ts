import { autoMatch, headersOf } from "./csv";

describe("reading a file's columns", () => {
  it("reads the header line, ignoring a byte-order mark and Windows line endings", () => {
    expect(headersOf("﻿store_id, name\r\nS01,Orlando\r\n")).toEqual(["store_id", "name"]);
  });
  it("matches names loosely and leaves out what it cannot match", () => {
    expect(autoMatch(["store_id", "name", "city"], ["Store ID", "NAME", "Lat"])).toEqual({ store_id: "Store ID", name: "NAME" });
  });
});
