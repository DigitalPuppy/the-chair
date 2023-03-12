dxld=16;
rm=0.1;
vm =0.2;

projection()
difference(){
union()
{
    cube([150,50,1]);
    translate([0, -35, 0]) cube([50,120,1]);
}
translate([12,-5, -5])cylinder(10, 8);
translate([37,-5, -5])cylinder(10, 8);
translate([12, 55, -5])cylinder(10, 8);
translate([37, 55, -5])cylinder(10, 8);

translate([12,-25, -5])cylinder(10, 8);
translate([37,-25, -5])cylinder(10, 8);
translate([12, 75, -5])cylinder(10, 8);
translate([37, 75, -5])cylinder(10, 8);

translate([130, 25-dxld/2, -5])cylinder(10, 3+vm);
translate([130, 25+dxld/2, -5])cylinder(10, 3+vm);

translate([15, 15, -5])cylinder(10, 3+rm);
translate([15, 35, -5])cylinder(10, 3+rm);
translate([35, 15, -5])cylinder(10, 3+rm);
translate([35, 35, -5])cylinder(10, 3+rm);
}