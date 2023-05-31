#include <dt-bindings/zmk/keys.h>

#define KEYS_L 0 1 2 3 4 10 11 12 13 14 15 22 23 24 25 26 27
#define KEYS_R 5 6 7 8 9 16 17 18 19 20 21 28 29 30 31 32 33
#define THUMBS 34 35 36 37 38 39

#define LT0 4
#define LT1 3
#define LT2 2
#define LT3 1
#define LT4 0

#define RT0 5
#define RT1 6
#define RT2 7
#define RT3 8
#define RT4 9

#define LM0 15
#define LM1 14
#define LM2 13
#define LM3 12
#define LM4 11
#define LM5 10

#define RM0 16
#define RM1 17
#define RM2 18
#define RM3 19
#define RM4 20
#define RM5 21

#define LB0 27
#define LB1 26
#define LB2 25
#define LB3 24
#define LB4 23
#define LB5 22

#define RB0 28
#define RB1 29
#define RB2 30
#define RB3 31
#define RB4 32
#define RB5 33

#define LH0 36
#define LH1 35
#define LH2 34

#define RH0 37
#define RH1 38
#define RH2 39

#define X_LM &bsdel
#define X_RM &kp TAB

#define X_LB &kp MINUS
#define X_RB &kp SQT

#define GAME_LAYER_KEYS\
           &kp TAB   &kp Q &kp W &kp E &kp R /**/ &none &kp N7 &kp N8 &kp N9 &kp N0\
  &kp BSPC &kp LCTL  &kp A &kp S &kp D &kp F /**/ &none &kp N4 &kp N5 &kp N6 &none  &kp RET\
  &kp ESC  &kp LSHFT &kp Z &kp X &kp C &kp V /**/ &none &kp N1 &kp N2 &kp N3 &none  &tog GAME\
                  &kp LALT &kp RET &kp SPACE /**/ &kp LSHFT &lt SYM RET  &kp SQT
