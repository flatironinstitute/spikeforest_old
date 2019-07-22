import React, { Component } from 'react';

class UnitDetailWidget extends Component {
    state = {  }
    
    async componentDidMount() {
        await this.updateData()
    }

    render() { 
        return (
            <div>UnitDetailWidget</div>
        );
    }
}
 
export default UnitDetailWidget;
