import React from "react";
import ReactDOM from "react-dom";
import MainWindow from "./components/MainWindow";

import 'bootstrap/dist/css/bootstrap.min.css';
import 'highlight.js/styles/railscasts.css';
import { createMuiTheme } from "@material-ui/core";
import { ThemeProvider } from "@material-ui/styles";
import { MuiThemeProvider } from "@material-ui/core/styles";
import { blue, green, red, yellow } from "@material-ui/core/colors";

const theme = createMuiTheme({
    overrides: {
        MuiTableRow: {
            root: {
                '&:hover': {
                    backgroundColor: '#CCCCCC'
                },
                '&$selected': {
                    backgroundColor: '#AAAAAA',
                    '&:hover': {
                        backgroundColor: '#BBBBBB'
                    }
                }
            }
        }
    }
});

const show_mtbrowser = async (path) => {
    ReactDOM.render((
        <MuiThemeProvider theme={theme}>
            <MainWindow path={path}>
            </MainWindow>
        </MuiThemeProvider>
    ),
        document.getElementById("root")
    );
};

const show_default_mtbrowser = async () => {
    // in future use key path here
    // const gallery_path = 'sha1dir://b950b6a3ec81d481b8c19b03a23e9a5747c71b38.gallery';
    const gallery_path = 'key://pairio/spikeforest/gallery';
    await show_mtbrowser(gallery_path);
}

window.show_mtbrowser = show_mtbrowser;
window.show_default_mtbrowser = show_default_mtbrowser;

show_default_mtbrowser();
