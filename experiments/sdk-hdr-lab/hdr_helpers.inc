// AEIG repair: explicit arithmetic domain, no claim of a universal HDR HSL.
static bool
AEIGHdrInputSupported(const PF_PixelFloat& p)
{
    const double limit = double((std::numeric_limits<PF_FpShort>::max)()) / 32.0;
    return std::isfinite(p.red) && std::isfinite(p.green) && std::isfinite(p.blue) &&
           std::isfinite(p.alpha) && std::fabs(double(p.red)) <= limit &&
           std::fabs(double(p.green)) <= limit && std::fabs(double(p.blue)) <= limit &&
           std::fabs(double(p.alpha)) <= limit;
}

static bool
AEIGHdrOutputSupported(double r, double g, double b)
{
    const double limit = double((std::numeric_limits<PF_FpShort>::max)());
    return std::isfinite(r) && std::isfinite(g) && std::isfinite(b) &&
           std::fabs(r) <= limit && std::fabs(g) <= limit && std::fabs(b) <= limit;
}

static PF_Err
AEIGHdrInvertYIQ(const PF_PixelFloat& input, PF_PixelFloat& output, A_long channel)
{
    // A uses the sample's decimal forward coefficients, now on unquantized RGB.
    // The inverse is adj(A)/det(A), not the sample's approximate reverse matrix.
    const double a = 0.2989, b = 0.5866, c = 0.1144;
    const double d = 0.5959, e = -0.2741, f = -0.3218;
    const double g = 0.2113, h = -0.5227, i = 0.3113;
    const double determinant = a*(e*i-f*h) - b*(d*i-f*g) + c*(d*h-e*g);
    double y = a*double(input.red) + b*double(input.green) + c*double(input.blue);
    double phase = d*double(input.red) + e*double(input.green) + f*double(input.blue);
    double quadrature = g*double(input.red) + h*double(input.green) + i*double(input.blue);
    switch (channel) {
        case Channel_YIQ: y = 1.0-y; phase = -phase; quadrature = -quadrature; break;
        case Channel_LUMINANCE: y = 1.0-y; break;
        case Channel_IN_PHASE_CHROMINANCE: phase = -phase; break;
        case Channel_QUADRATURE_CHROMINANCE: quadrature = -quadrature; break;
        default: return PF_Err_BAD_CALLBACK_PARAM;
    }
    const double r = ((e*i-f*h)*y + (c*h-b*i)*phase + (b*f-c*e)*quadrature) / determinant;
    const double green = ((f*g-d*i)*y + (a*i-c*g)*phase + (c*d-a*f)*quadrature) / determinant;
    const double blue = ((d*h-e*g)*y + (b*g-a*h)*phase + (a*e-b*d)*quadrature) / determinant;
    if (!AEIGHdrOutputSupported(r, green, blue)) return PF_Err_BAD_CALLBACK_PARAM;
    output.alpha = input.alpha;
    output.red = static_cast<PF_FpShort>(r);
    output.green = static_cast<PF_FpShort>(green);
    output.blue = static_cast<PF_FpShort>(blue);
    return PF_Err_NONE;
}
