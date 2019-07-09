import React from "react";
import FileContentView from "./FileContentView";

export default class FileContentViewPlugin {
    static getViewElementsForFile(path, opts) {
        return [<FileContentView path={path} size={opts.size}></FileContentView>];
    }
};
