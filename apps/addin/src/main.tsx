import React from "react";
import ReactDOM from "react-dom/client";
import TaskPane from "./TaskPane";

Office.onReady(() => {
  ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
    <React.StrictMode>
      <TaskPane />
    </React.StrictMode>,
  );
});
