#include <dt-bindings/zmk/keys.h>

#define KEYS_L 0 1 2 3 4 10 11 12 13 14 20 21 22 23 24
#define KEYS_R 5 6 7 8 9 15 16 17 18 19 25 26 27 28 29
#define THUMBS 30 31 32 33 34 35

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

#define LB0 24
#define LB1 23
#define LB2 22
#define LB3 21
#define LB4 20

#define RB0 25
#define RB1 26
#define RB2 27
#define RB3 28
#define RB4 29

#define LH0 32
#define LH1 31
#define LH2 30

#define RH0 33
#define RH1 34
#define RH2 35

#define GAME_LAYER_KEYS\
  &kp TAB &kp Q &kp W &kp E &kp R /**/ &kp T &kp Y &kp U &kp I &kp O\
  &kp CTL &kp A &kp S &kp D &kp F /**/ &kp G &kp H &kp J &kp K &kp L\
  &kp SFT &kp Z &kp X &kp C &kp V /**/ &kp B &kp M &kp N &kp P &kp SEMI\
    &lt NFN ESC &kp RET &kp SPACE /**/ &kp ALT &mo EXT &kp SQT
