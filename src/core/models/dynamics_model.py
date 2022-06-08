import numpy as np
from core.models.model import EnvironmentModel
from core.models.derived_models import DerivedStateModel
from typing import Dict, Any, Tuple
from core.state.state import State
from core.state.statetime import StateTime


class InertiaModel(DerivedStateModel):
    def evaluate(self, state: State) -> Dict[str, Any]:
        fill_frac = state.fill_frac

        dcm = np.array([[0, 1, 0], [0, 0, -1], [-1, 0, 0]], dtype=np.int32)
        dcmT = np.transpose(dcm)

        # Inertia tensor when full. Structure is:
        # [[Ixx, Ixy, Ixz],
        #  [Iyx, Iyy, Iyz],
        #  [Izx, Izy, Izz]].
        # Units are (kg * m^2).
        idf = (
            np.array(
                [
                    [933513642.20, 260948256.18, 430810000.30],
                    [260948256.18, 1070855457.07, 387172545.62],
                    [430810000.30, 387172545.62, 629606813.62],
                ],
                dtype=np.float64,
            )
            * 1e-9
        )
        idf_b = np.matmul(np.matmul(dcm, idf), dcmT)

        # Inertia tensor at 125 mL. Structure is:
        # [[Ixx, Ixy, Ixz],
        #  [Iyx, Iyy, Iyz],
        #  [Izx, Izy, Izz]].
        # Units are (kg * m^2).
        idi = (
            np.array(
                [
                    [855858994.14, 229481961.55, 377087149.13],
                    [229481961.55, 963124288.81, 353943859.15],
                    [377087149.13, 353943859.15, 559805590.96],
                ],
                dtype=np.float64,
            )
            * 1e-9
        )
        idi_b = np.matmul(np.matmul(dcm, idi), dcmT)

        # Determine inertia tensor for Oxygen via linear interpolation as a function of fill
        # fraction.

        # TODO: determine whether linear fit is accurate enough
        ioxy = (idf_b - idi_b) * fill_frac + idi_b

        return {
            "Ixx": ioxy[0][0],
            "Ixy": ioxy[0][1],
            "Ixz": ioxy[0][2],
            "Iyx": ioxy[1][0],
            "Iyy": ioxy[1][1],
            "Iyz": ioxy[1][2],
            "Izx": ioxy[2][0],
            "Izy": ioxy[2][1],
            "Izz": ioxy[2][2],
        }


class KaneModel(DerivedStateModel):
    """Calculates the Kane damping coefficient from 2016 simulation data by K. Doyle."""

    def evaluate(self, state: State) -> Dict[str, Any]:
        # Coefficients below are from Kyle's work.
        # TODO: Update them when we conduct a new Ansys analysis.
        k = 0.00085
        factor = 1.2

        N = 50
        kane = fill = tau1 = tau2 = np.zeros(N)
        for i in range(N):
            fill[i] = (i - 1) / N
            tau1[i] = k * fill[i]
            tau2[i] = factor * k * (1 - fill[i])
            kane[i] = -np.sqrt(tau1[i] ** 2 + tau2[i] ** 2)

        kane = kane - np.max(kane) + k
        kane = kane - np.min(kane)
        kane = kane * k / np.max(kane)

        q = np.round(state.fill_frac / 0.02 + 1)
        c = kane(q)

        return {"kane_c": c}


# # Maybe in another life...
# class LModel(EnvironmentModel):
#     """Class for the angular momentum model."""
#     def __init__(self, parameters: Parameters) -> None:
#         super().__init__(parameters)

#     def evaluate(self, state: State) -> Dict[str, Any]:
#         return super().evaluate(state)

#     def d_state(self, state: State) -> Dict[str, Any]:
#         ...


def cross_product_matrix(vector: np.ndarray) -> np.matrix:  # type: ignore
    """Creates a cross-multiplication matrix for a length 3 vector
    See bottom of page 2 of https://cornell.app.box.com/file/809903125394
    for brief reference.


    Args:
        vector (np.array): a 3x1 vector

    Returns:
        np.matrix: a 3x3 matrix which when matrix multiplied with another vector, b, has the same results as the input
        vector cross-product with b
    """

    return np.matrix(
        [[0, -vector[2], vector[1]], [vector[2], 0, -vector[0]], [-vector[1], vector[0], 0]]  # type: ignore
    )


def calc_xi(v: np.ndarray, r: float) -> np.matrix:
    """Xi function as defined on page 7 of https://cornell.app.box.com/file/809903125394

    Args:
        v (np.ndarray): 3-by-1 numpy array (column vector) representing the vector component of a quaternion.
        r (float): scalar component of the quaternion

    Returns:
        Numpy matrix: 4-by-3 Xi matrix
    """
    top = r * np.eye(3) + cross_product_matrix(v)  # 3-by-3 matrix
    bot = -v.T  # 1-by-3 matrix
    return np.matrix(np.vstack((top, bot)))  # stacked to be a 4-by-3


def calc_psi(v: np.ndarray, r: float) -> np.matrix:
    """Psi function as defined on page 7 of https://cornell.app.box.com/file/809903125394

    Args:
        v (np.ndarray):  3-by-1 numpy array (column vector) representing the vector component of a quaternion.
        r (float): scalar component of the quaternion

    Returns:
        np.matrix: 4-by-3 Psi matrix
    """
    top = r * np.eye(3) - cross_product_matrix(v)  # 3-by-3 matrix
    bot = -v.T  # 1-by-3 matrix
    return np.matrix(np.vstack((top, bot)))  # stacked to be a 4-by-3


def quat_to_dcm(quat: np.ndarray) -> np.matrix:
    """Calculates the direction cosine matrix (DCM) associated with the input quaternion.
    The math in this function is based off of page 17 of https://cornell.app.box.com/file/809903002605
    Args:
        quat (np.ndarray): 4x1 quaternion

    Returns:
        np.matrix: 3x3 Direction Cosine Matrix
    """

    v = quat[0:3]
    r = quat[3]

    xi = calc_xi(v, r)
    psi = calc_psi(v, r)

    dcm = np.matmul(xi.T, psi)

    return np.matrix(dcm)


def dcm_to_spherical_coords(
    dcm: np.matrix, spacecraft_frame_vector: np.ndarray = np.array((1, 0, 0))
) -> Tuple[float, float]:
    """Calculates the spherical coordinate components (theta, phi) of the `spacecraft_frame_vector` from the input
    spacecraft-body DCM.

    Args:
        dcm (np.matrix): the DCM of an ECI to spacecraft body frame transformation
        spacecraft_frame_vector (np.ndarray, optional): vector in the spacecraft body
        frame that is converted into ECI and then transformed into spherical coordinates.
        Defaults to np.array((1, 0, 0)).

    Returns:
        Tuple[float, float]: (theta, phi) angles corresponding to the spherical coordinates
    """
    vector_in_ECI_frame = np.matmul(dcm.T, spacecraft_frame_vector)
    normed_vec = vector_in_ECI_frame / np.linalg.norm(vector_in_ECI_frame)

    phi = np.arccos(normed_vec[2])
    theta = np.arctan2(normed_vec[1], normed_vec[0])
    return phi, theta


def quaternion_derivative(current_quat: np.ndarray, angular_velocity: np.ndarray) -> np.ndarray:
    """Calculates the time derivative of a given quaternion based on angular velocity.
    The algo implemented here is based off the math on page 17 of
    https://cornell.app.box.com/file/809903002605

    Args:
        current_quat (np.ndarray): length-4 array describing the quaternion of the spacecraft's angular position in ECI.
        (first 3 elements describe the vector, last one describes the scalar component)

        angular_velocity (np.ndarray): length-3 array of the angular velocities in rad/s (in the body frame, i think)

    Returns:
        np.ndarray: the time derivative of each element of the quaternion
    """

    current_quat.shape = (4, 1)  # enforces a column vector
    angular_velocity.shape = (3, 1)

    v = current_quat[0:3]
    r = current_quat[3]

    xi = calc_xi(v, r)

    quat_derivative = 0.5 * np.matmul(xi, angular_velocity)  # 4x3 times a 3x1 = 4x1

    return quat_derivative


class AttitudeDynamics(EnvironmentModel):
    """Class for the angular velocity and position model."""

    def d_state(self, state_time: StateTime) -> Dict[str, Any]:
        """Evaluates
        (tau)   =   [I_b d(omega_{B/N})/dt]
                +   [(omega_{B/N}) x (I_b (omega_{B/N}))]
                + c [(omega_{B/N}) - (omega_{D/N})]
        where c is the "Kane Damping" constant.


        """

        s = state_time.state
        # d = state_time.derived_state

        cur_quat = np.array([s.quat_v1, s.quat_v2, s.quat_v3, s.quat_r])
        angular_vel = np.array([s.ang_vel_x, s.ang_vel_y, s.ang_vel_z])

        d_quat = quaternion_derivative(cur_quat, angular_vel)
        # TODO: Use angular momentum as state variable and for most dynamics evaluation
        # then calculate angular rates from momenta b/c inertia matricies change over time

        return {"quat_v1": d_quat[0], "quat_v2": d_quat[1], "quat_v3": d_quat[2], "quat_r": d_quat[3]}
