import React, { Component } from 'react';
import { GridList, GridListTile } from '@material-ui/core';

const TopTable = (props) => {
    let { item } = props;
    if (!item.type) {
        return <div></div>;
    }
    let table;
    if (item.type === 'file') {
        let path0 = item.path;
        if (path0.endsWith('.json')) {
            path0 = <a href="#" onClick={() => { props.onOpenPath && props.onOpenPath(item.path) }}>{item.path}</a>;
        }
        table = <table className="table">
            <tbody>
                <tr>
                    <td>Path</td>
                    <td>{path0}</td>
                </tr>
                <tr>
                    <td>Size</td>
                    <td>{(item.data.file || {}).size}</td>
                </tr>
            </tbody>
        </table>;
    }
    else if (item.type === 'dir') {
        table = <table className="table">
            <tbody>
                <tr>
                    <td>Path</td>
                    <td><a href="#" onClick={() => { props.onOpenPath && props.onOpenPath(item.path) }}>{item.path}</a></td>
                </tr>
            </tbody>
        </table>;
    }
    else if (item.type === 'object') {
        table = <table className="table">
            <tbody>
                <tr>
                    <td>Item</td>
                    <td>{item.path}</td>
                </tr>
            </tbody>
        </table>;
    }
    else if (item.type === 'array-parent') {
        table = <table className="table">
            <tbody>
                <tr>
                    <td>Item</td>
                    <td>{item.path}</td>
                </tr>
            </tbody>
        </table>;
    }
    else if (item.type === 'value') {
        let val0 = item.data.value;
        if (isPath(val0)) {
            val0 = <a href="#" onClick={() => { props.onOpenPath && props.onOpenPath(item.data.value) }}>{item.data.value}</a>
        }
        table = <table className="table">
            <tbody>
                <tr>
                    <td>Item</td>
                    <td>{item.path}</td>
                </tr>
                <tr>
                    <td>Value</td>
                    <td>{val0}</td>
                </tr>
            </tbody>
        </table>;
    }
    else {
        table = <div>{`Unexpected item type ${item.type}`}</div>
    }
    return table;
}

function isPath(str0) {
    if (typeof (str0) != 'string') return false;
    return (str0.startsWith('sha1://') || str0.startsWith('sha1dir://') || str0.startsWith('key://'));
}

class ItemView extends Component {
    state = {
        pluginComponents: []
    }

    componentDidMount() {
        this.updatePluginComponents();
    }

    componentDidUpdate(prevProps) {
        if ((prevProps.item !== this.props.item) || (prevProps.viewPlugins !== this.props.viewPlugins)) {
            this.updatePluginComponents();
        }
    }

    updatePluginComponents() {
        let { item, viewPlugins, kacheryManager, onOpenPath, onSelectItem } = this.props;
        if (!item) return;
        if (!viewPlugins) return;
        let components = [];
        if (viewPlugins) {
            for (let plugin of viewPlugins) {
                let opts = {
                    kacheryManager: kacheryManager,
                    onOpenPath: onOpenPath,
                    onSelectItem: onSelectItem
                }
                if (item.type === 'file') {
                    if (plugin.getViewComponentsForFile) {
                        opts.size = item.data.file.size;
                        let components0 = plugin.getViewComponentsForFile(`sha1://${item.data.file.sha1}/${item.name}`, opts);
                        components.push(...components0);
                    }
                }
                else if (item.type === 'dir') {
                    if (plugin.getViewComponentsForDir) {
                        let components0 = plugin.getViewComponentsForDir(item.path, item.data.dir, opts);
                        components.push(...components0);
                    }
                }
                else if (item.type === 'object') {
                    if (plugin.getViewComponentsForObject) {
                        let components0 = plugin.getViewComponentsForObject(item.name, item.path, item.data.object, opts);
                        components.push(...components0);
                    }
                }
            }
        }
        this.setState({ pluginComponents: components });
    }

    getNumColsForSizeString(sizeString) {
        switch (sizeString) {
            case 'small':
                return 1;
            case 'large':
                return 2;
            default:
                return 1;
        }
    }

    render() {
        const item = this.props.item || {};
        const { pluginComponents } = this.state;
        return (
            <div style={{ padding: '10px' }}>
                <GridList cellHeight={'auto'} cols={2} spacing={10}>
                    <GridListTile cols={2}>
                        <TopTable
                            item={item}
                            onOpenPath={this.props.onOpenPath}
                        />
                    </GridListTile>
                    {
                        pluginComponents.map((comp, ii) => (
                            <GridListTile cols={this.getNumColsForSizeString(comp.size || 'small')} key={ii}>
                                <div>
                                    {comp.component}
                                </div>
                            </GridListTile>
                        ))
                    }
                </GridList>
            </div>
        );
    }
}

export default ItemView;