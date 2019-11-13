import React from "react";
import FileContentView from "./FileContentView";

export default class FileContentViewPlugin {
    static getViewComponentsForFile(path, opts) {
        return [{
            component: <FileContentView path={path} size={opts.size} showContent={false} key={path} kacheryManager={opts.kacheryManager}></FileContentView>,
            size: 'large'
        }];
    }
};
