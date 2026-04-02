#include <stdio.h>
#include <stdlib.h>

extern void initialize();
extern int alt_sep_test();

extern int Cur_Vertical_Sep;
extern int High_Confidence;
extern int Two_of_Three_Reports_Valid;
extern int Own_Tracked_Alt;
extern int Own_Tracked_Alt_Rate;
extern int Other_Tracked_Alt;
extern int Alt_Layer_Value;
extern int Up_Separation;
extern int Down_Separation;
extern int Other_RAC;
extern int Other_Capability;
extern int Climb_Inhibit;

int main() {
    initialize();

    if (scanf("%d %d %d %d %d %d %d %d %d %d %d %d",
        &Cur_Vertical_Sep,
        &High_Confidence,
        &Two_of_Three_Reports_Valid,
        &Own_Tracked_Alt,
        &Own_Tracked_Alt_Rate,
        &Other_Tracked_Alt,
        &Alt_Layer_Value,
        &Up_Separation,
        &Down_Separation,
        &Other_RAC,
        &Other_Capability,
        &Climb_Inhibit) != 12) {
        return 1;
    }

    printf("%d\n", alt_sep_test());
    return 0;
}
