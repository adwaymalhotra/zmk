#pragma once
#include "zmk-helpers/helper.h"

// Some More Simplifications
#define ZTHUMB(THUMB_L, THUMB_R) \
  X_LH THUMB_L X_MH THUMB_R X_RH

#define ZTLAYER(NAME, TOP, MIDDLE, BOTTOM, THUMB_L, THUMB_R, ...) \
  ZMK_LAYER(NAME, \
    X_LT TOP X_RT \
    X_LM MIDDLE X_RM \
    X_LB BOTTOM X_RB \
    ZTHUMB(THUMB_L, THUMB_R))

#define ZLAYER(NAME, TOP, MIDDLE, BOTTOM, ...) \
  ZTLAYER(NAME, TOP, MIDDLE, BOTTOM, LEFT_THUMBS, RIGHT_THUMBS)

#define TRANS_ROW &trans &trans &trans &trans &trans &trans &trans &trans &trans &trans
#define TRANS_LAYER(NAME) ZLAYER(NAME, TRANS_ROW, TRANS_ROW, TRANS_ROW)

#define ALT LALT
#define MET LGUI
#define SFT LSHFT
#define CTL LCTL
