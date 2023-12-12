#include <dt-bindings/zmk/keys.h>

#define KEYS_L 0 1 2 3 4 10 11 12 13 14 20 21 22 23 24 25
#define KEYS_R 5 6 7 8 9 15 16 17 18 19 26 27 28 29 30 31
#define THUMBS 32 33 34 35 36 37

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

#define LM0 14
#define LM1 13
#define LM2 12
#define LM3 11
#define LM4 10

#define RM0 15
#define RM1 16
#define RM2 17
#define RM3 18
#define RM4 19

#define LB0 25
#define LB1 24
#define LB2 23
#define LB3 22
#define LB4 21
#define LB5 20

#define RB0 26
#define RB1 27
#define RB2 28
#define RB3 29
#define RB4 30
#define RB5 31

#define LH0 34
#define LH1 33
#define LH2 32

#define RH0 35
#define RH1 36
#define RH2 37

#define X_LB &lt SYS TAB
#define X_RB &lt_bsdel SYS 0

#define GAME_LAYER_KEYS\
          &kp TAB   &kp Q &kp W &kp E &kp R /**/ &none &kp N7 &kp N8 &kp N9 &kp N0\
          &kp LCTL  &kp A &kp S &kp D &kp F /**/ &none &kp N4 &kp N5 &kp N6 &none\
  &kp ESC &kp LSHFT &kp Z &kp X &kp C &kp V /**/ &none &kp N1 &kp N2 &kp N3 &none  &tog GAME\
                 &kp LALT &kp RET &kp SPACE /**/ &kp LSHFT &kp RET  &kp SQT
