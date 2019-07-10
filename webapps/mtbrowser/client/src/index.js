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

const show_default_mtbrowser = async () => {
    const gallery_path = 'sha1dir://d55cf60dea55b7f33f83e7756237137f54667460.mtbrowser_gallery';
    await show_mtbrowser(gallery_path);
}

window.show_mtbrowser = show_mtbrowser;
window.show_default_mtbrowser = show_default_mtbrowser;
