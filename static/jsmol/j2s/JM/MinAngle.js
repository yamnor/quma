Clazz.declarePackage ("JM");
Clazz.load (["JM.MinObject"], "JM.MinAngle", null, function () {
var c$ = Clazz.decorateAsClass (function () {
this.sbType = 0;
this.sbKey = null;
this.ka = 0;
this.theta0 = NaN;
Clazz.instantialize (this, arguments);
}, JM, "MinAngle", JM.MinObject);
Clazz.makeConstructor (c$, 
function (data) {
Clazz.superConstructor (this, JM.MinAngle, []);
this.data = data;
}, "~A");
});
;//5.0.1-v2 Sat Nov 25 17:51:22 CST 2023
