window.FeatureSpaceModel=FeatureSpaceModel;

const Mda = window.Mda;

function FeatureSpaceModel(X, params) {
    var that = this;
    
    if (!params) params={samplerate:0};
    
    this.getChannelData = function(ch,t1,t2) {
        let ret=[];
        for (let t=t1; t<t2; t++) {
            ret.push(X.value(ch,t));
        }
        return ret;
    };
    this.numChannels = function() {
      return X.N1();
    };
    this.numTimepoints = function() {
      return X.N2();
    };
    this.getSampleRate = function() {
      return params.samplerate;
    }
}
