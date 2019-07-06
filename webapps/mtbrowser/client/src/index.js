import React from "react";
import ReactDOM from "react-dom";
import { MTBrowser } from "./widgets";

const show_mtbrowser = async (path) => {
    ReactDOM.render(
        <div>
            <MTBrowser path={path}></MTBrowser>
        </div>,
        document.getElementById("root")
    );
};

window.show_mtbrowser = show_mtbrowser;
